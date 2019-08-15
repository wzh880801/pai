 # OpenPAI Submitter

***OpenPAI Submitter*** is a Jupyter Notebook extension, created for easy-to-use job submission and management on OpenPAI clusters. Users can submit Jupyter job in one click, and manage recent jobs by a flexible dialog.

![](docs_img/submitter-1.gif)

## How to Install

This extension requires **Python 3+** and Jupyter Notebook to work. Make sure you are using Jupyter Notebook with a Python 3 kernel.

Please use the following commands to install this extension (Make sure you are in the correct `python` environment).

```bash
pip install --upgrade pip
git clone -b notebook-extension https://github.com/Microsoft/pai
cd pai/contrib/notebook-extension
python setup.py # add --user to avoid permission issues if necessary
```

This extension leverage the [`Python` SDK](https://github.com/microsoft/pai/tree/master/contrib/python-sdk) as the low level implementation. It will also be installed in above commands (use `-i` in of `setup.py` to avoid isntalling SDK).

Before starting, user needs to give the basic information of the clusters. User could run below `python` codes anywhere (e.g. in a notebook cell). During execution of this snippet of code, the extension will try to connect the cluster and fetch its basic configuration.

```python
from openpaisdk.core import ClusterList

# to add a cluster
cluster_cfg = {
    "cluster_alias": ..., # each cluster mush have an unique alias
    "pai_uri": ...,
    "user": ...,
    # for user/password authentication
    "password": ...,
    # for Azure AD authentication
    "token": ...,
}
ClusterList().load().add(cluster_cfg).save()

# to delete a cluster
ClusterList().load().delete(cluster_alias).save()
```

There are other ways to manage the clusters, see the [documentation of SDK](https://github.com/microsoft/pai/tree/master/contrib/python-sdk).

## Quick Start

Once installed, the extension will add two buttons on the notebook page, namely <img src="./docs_img/submit-button.png" style="height:20px;width:25px"> and <img src="./docs_img/job-button.png" style="height:20px;width:25px">.

Button <img src="./docs_img/submit-button.png" style="height:20px;width:25px"> is designed for job submission. You can click it and the detailed cluster information will be loaded. Then click ***Quick Submit***. The extension will do the following work for you:

- Pack all files in current folder as a .zip file, and upload it to the cluster by WebHDFS.
- Generate job settings automatically, then submit it.
- Wait until the notebook is ready.

The picture below shows the submission process:

![](docs_img/submitter-1.gif)

You can safely close the page when the extension is waiting. Once the notebook is ready, the submitter will show up and give you the notebook URL:

![](docs_img/submitter-2.gif)

**Note: The waiting process will take 5 to 10 minutes.** If you are not willing to wait, you could probably click the bottom link on the submitter to start a new session. The submitted job will not lose, you can click <img src="./docs_img/job-button.png" style="height:20px;width:25px"> to find it.

### Submit as Interactive Notebook v.s. Python File

You can submit jobs in two ways:
- as an ***interactive notebook***
- as a ***.py file***

It is easy to understand the differences. The interactive mode is a quick way for you to submit the notebook you work on locally to the cluster. The notebook will stay the same but have access to GPU resource on cluster. This mode is mainly designed for experimenting and debugging.

On the other hand, submitting the job as a Python file will firstly convert the notebook to a Python script, then execute the script directly. This mode is a good way for deployment and batch submitting.

<img src="docs_img/submit-form.png" style="width:65%;" />

### Quick Submit v.s. Download Config

Only the pre-defined resource and docker image settings are available, when you use the button *Quick Submit* to submit jobs. If you need different settings, you can click the button *Download Config* to get the job configuration file. Then import it on the web portal for further configuring.

## Job Management
![](docs_img/recent-jobs.gif)

Clicking <img src="./docs_img/job-button.png" style="height:20px;width:25px"> will open the *Recent Jobs* panel. **This panel records all jobs submitted by this extension on this machine** (If a job is submitted in a different way, it won't show up). The panel will show some basic information about your jobs. Also, it will show notebook URL **when the job is submitted as an interactive notebook, and the notebook is ready.** The panel will not show completed jobs by default, but you can use the upper-right toggle to find all jobs.

## How to Update or Uninstall

To update this extension, please use the following commands:
```bash
git clone -b notebook-extension https://github.com/Microsoft/pai
cd pai/contrib/notebook-extension
jupyter nbextension install openpai_submitter
jupyter nbextension enable openpai_submitter/main
```

To disable this extension, please use the following commands:
```bash
jupyter nbextension disable openpai_submitter/main
```

## Known Issues
- This extension is not compatible with *Variable Inspector*.

## Feedback

Please use this [link](https://github.com/microsoft/pai/issues/new?title=[Jupyter%20Extension%20Feedback]) for feedbacks.