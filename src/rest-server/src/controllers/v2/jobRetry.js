// Copyright (c) Microsoft Corporation
// All rights reserved.
//
// MIT License
//
// Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated
// documentation files (the "Software"), to deal in the Software without restriction, including without limitation
// the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and
// to permit persons to whom the Software is furnished to do so, subject to the following conditions:
// The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.
//
// THE SOFTWARE IS PROVIDED *AS IS*, WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING
// BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
// NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM,
// DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
// OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

// module dependencies
const _ = require('lodash');
const asyncHandler = require('@pai/middlewares/v2/asyncHandler');
const jobRetry = require('@pai/models/v2/jobRetry.js');

const healthCheck = asyncHandler(async (req, res) => {
  const isHealthy = await jobRetry.healthCheck();
  if (!isHealthy) {
    res.status(501).send('Not healthy');
  } else {
    res.status(200).send('ok');
  }
});

const list = asyncHandler(async (req, res) => {
  const result = await jobRetry.list(req.params.frameworkName);
  res.status(result.status).json(result.data);
});

const get = asyncHandler(async (req, res) => {
  // const data = await jobRetry.get(
  //   req.params.frameworkName,
  //   req.params.jobRetryIndex,
  // );
  res
    .status(200)
    .send(`get ${req.params.frameworkName} ${req.params.jobRetryIndex}`);
});

// module exports
module.exports = {
  healthCheck,
  list,
  get,
};
