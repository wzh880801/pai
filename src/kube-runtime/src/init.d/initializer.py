#!/usr/bin/env python
# Copyright (c) Microsoft Corporation
# All rights reserved.
#
# MIT License
#
# Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated
# documentation files (the "Software"), to deal in the Software without restriction, including without limitation
# the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and
# to permit persons to whom the Software is furnished to do so, subject to the following conditions:
# The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED *AS IS*, WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING
# BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
# NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM,
# DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

import os
import sys
import copy
import logging
import argparse
import subprocess
import re

import yaml

sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from common.utils import init_logger  #pylint: disable=wrong-import-position

LOGGER = logging.getLogger(__name__)

EXIT_PLUGIN_INVALIDATE = 100
RUNTIME_PLUGIN_PLACE_HOLDER = "com.microsoft.pai.runtimeplugin"


def run_script(script_path, parameters, plugin_scripts):
    args = [sys.executable, script_path, "{}".format(parameters)]
    args += plugin_scripts
    proc = subprocess.Popen(args,
                            stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT)
    while True:
        line = proc.stdout.readline()
        if not line:
            break
        line = line.decode("UTF-8").strip()
        LOGGER.info(line)
    proc.wait()
    if proc.returncode:
        LOGGER.error("failed to run %s, error code is %s", script_path,
                     proc.returncode)
        raise Exception("Failed to run init script")


def _prune_plugins(job_config):
    """prune plugins according to the env.

    Args:
        job_config: Job config object generated by parser.py from framework.json.
    Return:
        pruned job config
    """
    pruned_config = copy.deepcopy(job_config)
    if "extras" not in job_config or RUNTIME_PLUGIN_PLACE_HOLDER not in job_config[
            "extras"]:
        return pruned_config
    gang_allocation = os.environ.get("GANG_ALLOCATION", "true")

    if gang_allocation == "true":
        return pruned_config

    delete_plugin_names = []
    plugins = job_config["extras"][RUNTIME_PLUGIN_PLACE_HOLDER]
    for plugin in plugins:
        plugin_name = plugin["plugin"]
        if plugin_name == "ssh":
            LOGGER.warning(
                'ssh plugin is conflict with gang allocation, will remove ssh plugin'
            )
            delete_plugin_names.append(plugin_name)

    pruned_config["extras"][RUNTIME_PLUGIN_PLACE_HOLDER] = list(
        filter(lambda plugin: plugin["plugin"] not in delete_plugin_names,
               plugins))
    return pruned_config


def init_deployment(jobconfig, commands, taskrole):
    """Inject preCommands and postCommands form deployment.

    Args:
        jobconfig: Jobconfig object generated by parser.py from framework.json.
        commands: Commands to call in precommands.sh and postcommands.sh.
    """

    if "defaults" not in jobconfig or "deployments" not in jobconfig or "deployment" not in jobconfig[
            "defaults"]:
        LOGGER.info("No suitable deployment found in jobconfig. Skipping")
        return

    deployment_name = jobconfig["defaults"]["deployment"]
    for deployment in jobconfig["deployments"]:
        if deployment["name"] == deployment_name and taskrole in deployment[
                "taskRoles"]:
            # Inject preCommands and postCommands
            if "preCommands" in deployment["taskRoles"][taskrole]:
                commands[0].append("\n".join(
                    deployment["taskRoles"][taskrole]["preCommands"]))
            if "postCommands" in deployment["taskRoles"][taskrole]:
                commands[1].insert(
                    0, "\n".join(
                        deployment["taskRoles"][taskrole]["postCommands"]))


def init_plugins(jobconfig, commands, plugins_path, runtime_path, taskrole):
    """Init plugins from jobconfig.

    Args:
        jobconfig: Jobconfig object generated by parser.py from framework.json.
        commands: Commands to call in precommands.sh and postcommands.sh.
        plugins_path: The base path for all plugins.
        output_path: The output path of plugin generated scripts.
    """
    if "extras" not in jobconfig or RUNTIME_PLUGIN_PLACE_HOLDER not in jobconfig[
            "extras"]:
        return None

    for index in range(len(jobconfig["extras"][RUNTIME_PLUGIN_PLACE_HOLDER])):
        plugin = jobconfig["extras"][RUNTIME_PLUGIN_PLACE_HOLDER][index]

        plugin_name = plugin["plugin"]
        plugin_base_path = "{}/{}".format(plugins_path, plugin_name)

        parameters = yaml.safe_load(
            replace_ref(str(plugin.get("parameters", "")), jobconfig,
                        taskrole))
        plugin["parameters"] = parameters

        with open("{}/desc.yaml".format(plugin_base_path), "r") as f:
            plugin_desc = yaml.safe_load(f)

        plugin_scripts = [
            "{}/plugin_pre{}.sh".format(runtime_path, index),
            "{}/plugin_post{}.sh".format(runtime_path, index)
        ]

        # Run init script
        if "init-script" in plugin_desc:
            run_script(
                "{}/{}".format(plugin_base_path, plugin_desc["init-script"]),
                yaml.safe_dump(plugin), plugin_scripts)

        if os.path.isfile(plugin_scripts[0]):
            commands[0].append("/bin/bash {}".format(plugin_scripts[0]))

        if os.path.isfile(plugin_scripts[1]):
            commands[1].insert(0, "/bin/bash {}".format(plugin_scripts[1]))
        return plugin_scripts


def replace_ref(param_str, jobconfig, taskrole):
    def _find_ref(matched):
        ref_str = re.sub(r'(\s*)%>', "",
                         re.sub(r'<%(\s*)\$', "", matched.group(0)))
        ref = ref_str.split(".")
        if ref[0] in ["parameters", "secrets"]:
            cur_element = jobconfig[ref[0]]
        elif ref[0] in ["script", "output", "data"]:
            cur_element = next(
                b for b in jobconfig["prerequisites"] if b["type"] == ref[0]
                and b["name"] == jobconfig["taskRoles"][taskrole][ref[0]])
        for i in range(1, len(ref)):
            list_indexes = re.findall(r'([\s\S]*?)\[(\s*)([0-9]+)(\s*)\]',
                                      ref[i])
            if not list_indexes:
                cur_element = cur_element[ref[i]]
            else:
                for list_index in list_indexes:
                    if list_index[0]:
                        cur_element = cur_element[list_index[0]]
                    cur_element = cur_element[int(list_index[2])]
        return cur_element

    replaced = re.sub(r'<%(\s*)\$([\s\S]*?)(\s*)%>', _find_ref, param_str)
    return replaced


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "jobconfig_yaml",
        help="jobConfig.yaml generated by parser.py from framework.json")
    parser.add_argument("plugins_path", help="Plugins path")
    parser.add_argument("runtime_path", help="Runtime path")
    parser.add_argument("task_role", help="container task role name")
    args = parser.parse_args()

    LOGGER.info("loading yaml from %s", args.jobconfig_yaml)
    with open(args.jobconfig_yaml) as j:
        job_config = yaml.load(j, Loader=yaml.SafeLoader)

    pruned_config = _prune_plugins(job_config)

    commands = [[], []]
    init_plugins(pruned_config, commands, args.plugins_path, args.runtime_path,
                 args.task_role)

    # pre-commands and post-commands already handled by rest-server.
    # Don't need to do this unless use commands in JobConfig for comments compatibility.
    # init_deployment(jobconfig, commands)

    with open("{}/precommands.sh".format(args.runtime_path), "a+") as f:
        f.write("\n".join(commands[0]))

    with open("{}/postcommands.sh".format(args.runtime_path), "a+") as f:
        f.write("\n".join(commands[1]))


if __name__ == "__main__":
    init_logger()
    main()
