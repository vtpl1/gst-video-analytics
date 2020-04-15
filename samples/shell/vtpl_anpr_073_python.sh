#!/bin/bash
# ==============================================================================
# Copyright (C) 2018-2020 Intel Corporation
#
# SPDX-License-Identifier: MIT
# ==============================================================================

set -e

BASEDIR=$(dirname "$0")/../..
if [ -n ${GST_SAMPLES_DIR} ]; then
  source $BASEDIR/scripts/setup_env.sh
fi
source $BASEDIR/scripts/setlocale.sh
source $BASEDIR/scripts/path_extractor.sh

# if [ -z ${1} ]; then
#   echo "ERROR set path to video"
#   echo "Usage: ./vtpl_anpr_073_python.sh <path/to/your/video/sample>"
#   exit
# fi

INPUT=file:///root/video-examples/ANPR/1.AVI

#MODEL1=frozen_073

#MODEL1_PROC=mo073_model_proc

MODEL1=onnx_124

MODEL1_PROC=mo073_onnx_124_model_proc

MODEL2=frozen_061

MODEL2_PROC=mo061_model_proc

DEVICE=CPU
PRE_PROC=ie

DETECT_MODEL_PATH=$(GET_MODEL_PATH $MODEL1 )
OCR_MODEL_PATH=$(GET_MODEL_PATH $MODEL2 )

echo Running sample with the following parameters:
echo GST_PLUGIN_PATH=${GST_PLUGIN_PATH}
echo LD_LIBRARY_PATH=${LD_LIBRARY_PATH}
export GST_DEBUG="*:2"
PYTHONPATH=$PYTHONPATH:$BASEDIR/python:$BASEDIR/samples/python \
LD_LIBRARY_PATH=$LD_LIBRARY_PATH:$GST_PLUGIN_PATH \
python3 $(dirname "$0")/vtpl_anpr_073_python.py -i ${INPUT} \
    -d=${DETECT_MODEL_PATH} \
    -d_p=$(PROC_PATH $MODEL1_PROC) \
    -d_2=${OCR_MODEL_PATH} \
    -d_2_p=$(PROC_PATH $MODEL2_PROC) \
