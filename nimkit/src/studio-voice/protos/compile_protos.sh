#!/bin/bash

# Copyright (c) 2024 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
#
# Permission is hereby granted, free of charge, to any person obtaining a
# copy of this software and associated documentation files (the "Software"),
# to deal in the Software without restriction, including without limitation
# the rights to use, copy, modify, merge, publish, distribute, sublicense,
# and/or sell copies of the Software, and to permit persons to whom the
# Software is furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL
# THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
# FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
# DEALINGS IN THE SOFTWARE.


# This script compiles Protocol Buffer (protobuf) definitions for NVIDIA
# Maxine Studio Voice on a Linux Client.
#
# Execute the script using `./compile_proto.sh`
#
# For more details, refer to README.md

SCRIPT_DIR="$(dirname "$(readlink -f "$0")")"
PROTOS_DIR=$SCRIPT_DIR/proto/nvidia/maxine/studiovoice/v1
OUT_DIR=$SCRIPT_DIR/../interfaces/studio_voice

python3 -m grpc_tools.protoc -I=$PROTOS_DIR \
                             --python_out=$OUT_DIR \
                             --pyi_out=$OUT_DIR \
                             --grpc_python_out=$OUT_DIR \
                             $PROTOS_DIR/studiovoice.proto
