xhost +
docker run -it --rm --privileged --net=host --device /dev/dri \
    \
    -v ~/.Xauthority:/root/.Xauthority \
    -v /tmp/.X11-unix:/tmp/.X11-unix \
    -e DISPLAY=$DISPLAY \
    -e HTTP_PROXY=$HTTP_PROXY \
    -e HTTPS_PROXY=$HTTPS_PROXY \
    -e http_proxy=$http_proxy \
    -e https_proxy=$https_proxy \
    \
    -v ~/gva/data/models/intel:/root/intel_models:ro \
    -v ~/gva/data/models/common:/root/common_models:ro \
    -e MODELS_PATH=/root/intel_models:/root/common_models \
    \
    -v ~/gva/data/video:/root/video-examples:ro \
    -e VIDEO_EXAMPLES_DIR=/root/video-examples \
    \
    -v ~/WorkFiles/vtpl1/gst-video-analytics:/root/gst-video-analytics \
    \
    vtpl/gst-video-analytics

#./samples/shell/face_detection_and_classification.sh $VIDEO_EXAMPLES_DIR/3.mp4
#./scripts/build.sh
