#!/bin/bash
# ==============================================================================
# Copyright (C) 2018-2020 Intel Corporation
#
# SPDX-License-Identifier: MIT
# ==============================================================================

set -e

BASEDIR=$(dirname "$0")/../..
if [ -n ${GST_SAMPLES_DIR} ]
then
    source $BASEDIR/scripts/setup_env.sh
fi
source $BASEDIR/scripts/setlocale.sh

#import GET_MODEL_PATH and PROC_PATH
source $BASEDIR/scripts/path_extractor.sh

if [ -z ${1} ]; then
  echo "ERROR set path to video"
  echo "Usage: ./vehicle_and_pedestrian_classification.sh <path/to/your/video/sample>"
  exit
fi

INPUT=${1}

MODEL1=person-vehicle-bike-detection-crossroad-0078
MODEL2=person-attributes-recognition-crossroad-0230
MODEL3=vehicle-attributes-recognition-barrier-0039

MODEL1_PROC=person-vehicle-bike-detection-crossroad-0078
MODEL2_PROC=person-attributes-recognition-vtpl-app
MODEL3_PROC=vehicle-attributes-recognition-vtpl-app

DEVICE=CPU
PRE_PROC=ie

DETECT_MODEL_PATH=$(GET_MODEL_PATH $MODEL1 )
CLASS_MODEL_PATH=$(GET_MODEL_PATH $MODEL2 )
CLASS_MODEL_PATH1=$(GET_MODEL_PATH $MODEL3 )

echo Running sample with the following parameters:
echo GST_PLUGIN_PATH=${GST_PLUGIN_PATH}
echo LD_LIBRARY_PATH=${LD_LIBRARY_PATH}
if [[ $INPUT == "/dev/video"* ]]; then
  SOURCE_ELEMENT="v4l2src device=${INPUT}"
elif [[ $INPUT == "rtsp://"* ]]; then
  SOURCE_ELEMENT="urisourcebin uri=${INPUT}"
else
  SOURCE_ELEMENT="filesrc location=${INPUT}"
fi

gst-launch-1.0 --gst-plugin-path ${GST_PLUGIN_PATH} \
  ${SOURCE_ELEMENT} ! decodebin ! videoconvert ! video/x-raw,format=BGRx ! \
  gvadetect inference-id=inf_detect model=$DETECT_MODEL_PATH model-proc=$(PROC_PATH $MODEL1_PROC) device=$DEVICE pre-proc=$PRE_PROC ! queue ! \
  gvadetect inference-id=inf_detect2 model=$DETECT_MODEL_PATH model-proc=$(PROC_PATH $MODEL1_PROC) device=$DEVICE pre-proc=$PRE_PROC ! queue ! \
  gvatrack tracking-type=iou ! queue ! \
  gvaclassify inference-id=inf_classify1 model=$CLASS_MODEL_PATH model-proc=$(PROC_PATH $MODEL2_PROC) device=$DEVICE pre-proc=$PRE_PROC object-class=person ! queue ! \
  gvaclassify inference-id=inf_classify2 model=$CLASS_MODEL_PATH1 model-proc=$(PROC_PATH $MODEL3_PROC) device=$DEVICE pre-proc=$PRE_PROC object-class=vehicle ! queue ! \
  gvawatermark ! videoconvert ! gvafpscounter ! fakesink sync=false