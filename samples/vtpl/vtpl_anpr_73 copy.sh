gst-launch-1.0 uridecodebin uri=file:///root/video-examples/ANPR/1.AVI ! \
    videoconvert ! capsfilter caps="video/x-raw,format=BGRx" ! \
    gvadetect model-instance-id=inf_detect model=/root/common_models/onnx_9_models/onnx_124.xml model-proc=./mo073_onnx_124_model_proc.json device=GPU threshold=0.25 ! queue ! \
    gvatrack tracking-type=short-term ! queue ! \
    gvadetect model-instance-id=inf_detect_ocr model=/root/common_models/061/ie/FP32/frozen_061.xml model-proc=./mo061_model_proc.json device=GPU is-full-frame=false object-class="LP" ! queue ! \
    gvawatermark name=gvawatermark ! videoconvert ! gvafpscounter ! fakesink