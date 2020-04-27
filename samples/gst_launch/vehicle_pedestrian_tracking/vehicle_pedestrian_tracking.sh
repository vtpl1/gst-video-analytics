#!/bin/bash
# ==============================================================================
# Copyright (C) 2020 Intel Corporation
#
# SPDX-License-Identifier: MIT
# ==============================================================================

set -e

# input parameters
FILE=${1:-https://github.com/intel-iot-devkit/sample-videos/raw/master/person-bicycle-car-detection.mp4}
DETECTION_INTERVAL=${2:-10}
INFERENCE_PRECISION=${3:-"FP32"}
DECODE_DEVICE=${4:-CPU}
INFERENCE_DEVICE=${5:-GPU}

MODEL_1=person-vehicle-bike-detection-crossroad-0078
MODEL_2=person-attributes-recognition-crossroad-0230
MODEL_3=vehicle-attributes-recognition-barrier-0039

TRACKING_TYPE="short-term"

RECLASSIFY_INTERVAL=10

if [[ $FILE == "/dev/video"* ]]; then
  SOURCE_ELEMENT="v4l2src device=${FILE}"
elif [[ $FILE == *"://"* ]]; then
  SOURCE_ELEMENT="urisourcebin buffer-size=4096 uri=${FILE}"
else
  SOURCE_ELEMENT="filesrc location=${FILE}"
fi

if [ $DECODE_DEVICE == CPU ]; then
  unset GST_VAAPI_ALL_DRIVERS
  VIDEO_PROCESSING="decodebin ! videoconvert ! video/x-raw,format=BGRx"
  PRE_PROC=ie
else
  export GST_VAAPI_ALL_DRIVERS=1
  VIDEO_PROCESSING="decodebin ! vaapipostproc ! video/x-raw(memory:VASurface)"
  PRE_PROC=vaapi
fi

GET_MODEL_PATH() {
    model_name=$1
    precision=${INFERENCE_PRECISION}
    for models_dir in ${MODELS_PATH//:/ }; do
        paths=$(find $models_dir -type f -name "*$model_name.xml" -print)
        if [ ! -z "$paths" ];
        then
            considered_precision_paths=$(echo "$paths" | grep "/$precision/")
           if [ ! -z "$considered_precision_paths" ];
            then
                echo $(echo "$considered_precision_paths" | head -n 1)
                exit 0
            else
                echo $(echo "$paths" | head -n 1)
                exit 0
            fi
        fi
    done

    echo -e "\e[31mModel $model_name file was not found. Please set MODELS_PATH\e[0m" 1>&2
    exit 1
}

PROC_PATH() {
    echo $(dirname "$0")/model_proc/$1.json
}

DETECTION_MODEL=$(GET_MODEL_PATH $MODEL_1)
PERSON_CLASSIFICATION_MODEL=$(GET_MODEL_PATH $MODEL_2)
VEHICLE_CLASSIFICATION_MODEL=$(GET_MODEL_PATH $MODEL_3)

DETECTION_MODEL_PROC=$(PROC_PATH $MODEL_1)
PERSON_CLASSIFICATION_MODEL_PROC=$(PROC_PATH $MODEL_2)
VEHICLE_CLASSIFICATION_MODEL_PROC=$(PROC_PATH $MODEL_3)

PIPELINE="gst-launch-1.0 \
  ${SOURCE_ELEMENT} ! ${VIDEO_PROCESSING} ! \
  gvadetect model=$DETECTION_MODEL \
            model-proc=$DETECTION_MODEL_PROC \
            inference-interval=${DETECTION_INTERVAL} \
            threshold=0.6 \
            pre-process-backend=${PRE_PROC} \
            device=${INFERENCE_DEVICE} ! \
  queue ! \
  gvatrack tracking-type=${TRACKING_TYPE} ! \
  queue ! \
  gvaclassify model=$PERSON_CLASSIFICATION_MODEL \
              model-proc=$PERSON_CLASSIFICATION_MODEL_PROC \
              reclassify-interval=${RECLASSIFY_INTERVAL} \
              pre-process-backend=${PRE_PROC} \
              device=${INFERENCE_DEVICE} object-class=person ! \
  queue ! \
  gvaclassify model=$VEHICLE_CLASSIFICATION_MODEL \
              model-proc=$VEHICLE_CLASSIFICATION_MODEL_PROC \
              reclassify-interval=${RECLASSIFY_INTERVAL} \
              pre-process-backend=${PRE_PROC} \
              device=${INFERENCE_DEVICE} object-class=vehicle ! \
  queue ! \
  gvawatermark ! videoconvert ! fpsdisplaysink video-sink=xvimagesink sync=true"

echo ${PIPELINE}
${PIPELINE}
