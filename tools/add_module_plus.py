#!/usr/bin/env python3
#
# Copyright 2021 The Bazel Authors. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# pylint: disable=invalid-name
# pylint: disable=line-too-long
# pylint: disable=missing-function-docstring
"""An interactive script to add modules into a Bazel registry.

What this script can do:
  - Initialize the Bazel Registry.
  - Generate/update the metadata.json for a module.
  - Add specified MODULE.bazel
  - Generate MODULE.bazel file with given module information
    - module name
    - version
    - compatibility level
    - dependencies
  - Generate the source.json file with given source information
    - The archive url
    - patch files
  - Add specified BUILD file for non-Bazel project by turning it into a patch.
  - Add specified presubmit.yml file.
  - Generate presubmit.yml file by given build & test targets.

"""

import argparse
import os
import sys
import json

from registry import Module
from registry import RegistryClient
from registry import log

import bcr_validation

YELLOW = "\x1b[33m"
RESET = "\x1b[0m"


def main(argv=None):
    if argv is None:
        argv = sys.argv[1:]

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--registry",
        type=str,
        default=".",
        help=
        "Specify the root path of the registry (default: the current working directory).",
    )
    parser.add_argument(
        "--input",
        type=str,
        help=
        "Take module information from a json file, which can be generated from previous input.",
    )

    args = parser.parse_args(argv)

    log(f"Getting module information from {args.input}...")
    with open(args.input) as f:
        module_data = json.load(f)
    module = Module()
    module.__dict__ = module_data["module"]
    homepage = module_data["homepage"]
    maintainers = module_data["maintainers"]
    source_repository = ""
    if module.url.startswith("https://github.com/"):
        parts = module.url.split("/")
        source_repository = "github:" + parts[3] + "/" + parts[4]

    client = RegistryClient(args.registry)
    client.init_module(module.name, maintainers, homepage, source_repository)
    client.add(module, override=True)
    log(f"{module.name} {module.version} is added into the registry.")

    log(f"Running ./tools/bcr_validation.py --check={module.name}@{module.version} --fix"
        )
    bcr_validation.main([f"--check={module.name}@{module.version}", "--fix"])


if __name__ == "__main__":
    # Under 'bazel run' we want to run within the source folder instead of the execroot.
    if os.getenv("BUILD_WORKSPACE_DIRECTORY"):
        os.chdir(os.getenv("BUILD_WORKSPACE_DIRECTORY"))
    sys.exit(main())
