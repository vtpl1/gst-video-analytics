set -e

if [ -z ${1} ]; then
  echo "ERROR set path to video"
  echo "Usage : ./vtpl_anpr_73.sh VIDEO_FILE [DECODE_DEVICE] [INFERENCE_DEVICE] [CHANNELS_COUNT]"
  exit
fi

FILE=${1}
DECODE_DEVICE=${2:-CPU}
INFERENCE_DEVICE=${3:-CPU}
CHANNELS_COUNT=${4:-1}

# MODEL=onnx_124
# MODEL_POST_PROC=mo073_onnx_124

MODEL=frozen_073
MODEL_POST_PROC=mo073

OCR_MODEL=frozen_061
OCR_MODEL_POST_PROC=mo061

TRACKING_TYPE="short-term"


if [[ $FILE == "/dev/video"* ]]; then
  SOURCE_ELEMENT="v4l2src device=${FILE}"
elif [[ $FILE == *"://"* ]]; then
  SOURCE_ELEMENT="urisourcebin buffer-size=4096 uri=${FILE}"
else
  SOURCE_ELEMENT="filesrc location=${FILE}"
fi

GET_MODEL_PATH() {
    model_name=$1
    precision="FP32"
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

DETECT_MODEL_PATH=$(GET_MODEL_PATH $MODEL )
DETECT_POST_PROC_PATH="./model_proc/${MODEL_POST_PROC}_model_proc.json"

OCR_MODEL_PATH=$(GET_MODEL_PATH $OCR_MODEL )
OCR_POST_PROC_PATH="./model_proc/${OCR_MODEL_POST_PROC}_model_proc.json"

if [ $DECODE_DEVICE == CPU ]; then
  unset GST_VAAPI_ALL_DRIVERS
  VIDEO_PROCESSING="decodebin ! videoconvert ! video/x-raw,format=BGRx"
  PRE_PROC=ie
else
  export GST_VAAPI_ALL_DRIVERS=1
  VIDEO_PROCESSING="decodebin ! vaapipostproc ! video/x-raw(memory:VASurface)"
  PRE_PROC=vaapi
fi

PIPELINE=" ${SOURCE_ELEMENT} ! ${VIDEO_PROCESSING} ! \
gvadetect model=${DETECT_MODEL_PATH} \
model-instance-id=inf0 device=${INFERENCE_DEVICE} \
pre-process-backend=${PRE_PROC} model-proc=${DETECT_POST_PROC_PATH} ! \
queue ! \
gvawatermark name=gvawatermark ! videoconvert ! \
gvafpscounter ! \
fpsdisplaysink video-sink=xvimagesink sync=false "

FINAL_PIPELINE_STR=""

for (( CURRENT_CHANNELS_COUNT=0; CURRENT_CHANNELS_COUNT < $CHANNELS_COUNT; ++CURRENT_CHANNELS_COUNT ))
do
  FINAL_PIPELINE_STR+=$PIPELINE
done


echo "gst-launch-1.0 ${FINAL_PIPELINE_STR}"
gst-launch-1.0 ${FINAL_PIPELINE_STR}


# gst-launch-1.0 uridecodebin uri=file:///root/video-examples/ANPR/1.AVI ! \
#     vaapipostproc ! capsfilter caps="video/x-raw(memory:VASurface)" ! \
#     gvadetect model-instance-id=inf_detect model=/root/common_models/onnx_9_models/onnx_124.xml model-proc=./mo073_onnx_124_model_proc.json device=GPU pre-process-backend=vaapi threshold=0.25 ! queue ! \
#     gvatrack tracking-type=short-term ! queue ! \
#     gvadetect model-instance-id=inf_detect_ocr model=/root/common_models/061/ie/FP32/frozen_061.xml model-proc=./mo061_model_proc.json device=GPU is-full-frame=false object-class="LP" pre-process-backend=vaapi ! queue ! \
#     gvafpscounter ! fakesink