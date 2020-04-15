# ==============================================================================
# Copyright (C) 2018-2020 Intel Corporation
#
# SPDX-License-Identifier: MIT
# ==============================================================================

import sys
import numpy
import cv2
from argparse import ArgumentParser

import gi

gi.require_version('GObject', '2.0')
gi.require_version('Gst', '1.0')
gi.require_version('GstApp', '1.0')
gi.require_version('GstVideo', '1.0')

from gi.repository import Gst, GObject, GstApp, GstVideo, GLib
from gstgva import VideoFrame, util

parser = ArgumentParser(add_help=False)
_args = parser.add_argument_group('Options')
_args.add_argument("-i", "--input", help="Required. Path to input video file",
                   default="file:///root/video-examples/ANPR/1.AVI",
                   required=False, type=str)
_args.add_argument("-d", "--detection_model",
                   default="/root/common_models/073/ie/FP32/frozen_073.xml",
                   required=True, type=str)
_args.add_argument("-d_p", "--detection_post_processing",
                   default="/root/gst-video-analytics/scripts/../samples/model_proc/mo073_model_proc.json",
                   required=True, type=str)
_args.add_argument("-d_2", "--detection_ocr_model",
                   default="/root/common_models/073/ie/FP32/frozen_061.xml",
                   required=True, type=str)
_args.add_argument("-d_2_p", "--detection_ocr_post_processing",
                   default="/root/gst-video-analytics/scripts/../samples/model_proc/mo061_model_proc.json",
                   required=True, type=str)

args = parser.parse_args()
global_pipeline = None

def create_launch_string():
    return 'uridecodebin uri={} ! \
    videoconvert ! capsfilter caps=\"video/x-raw,format=BGRx\" ! \
    gvadetect inference-id=inf_detect model={} model-proc={} device=CPU pre-proc=ie threshold=0.25 ! queue ! \
    gvatrack tracking-type=iou ! queue ! \
    gvadetect inference-id=inf_detect_ocr model={} model-proc={} device=CPU pre-proc=ie is-full-frame=false object-class="LP" ! queue ! \
    gvawatermark name=gvawatermark ! videoconvert ! gvafpscounter ! \
    fakesink sync=false'.format(args.input, 
                                args.detection_model,
                                args.detection_post_processing,
                                args.detection_ocr_model,
                                args.detection_ocr_post_processing)

def create_launch_string1():
    return 'uridecodebin uri={} ! \
    videoconvert ! capsfilter caps=\"video/x-raw,format=BGRx\" ! \
    gvadetect inference-id=inf_detect model={} model-proc={} device=CPU pre-proc=ie threshold=0.25 ! queue ! \
    gvatrack tracking-type=iou ! queue ! \
    gvawatermark name=gvawatermark ! videoconvert ! gvafpscounter ! \
    fakesink sync=false'.format(args.input, 
                                args.detection_model,
                                args.detection_post_processing)
def gobject_mainloop():
    #mainloop = GLib.MainLoop.new(None,False)
    mainloop = GLib.MainLoop()
    try:
        mainloop.run()
    except KeyboardInterrupt:
        print("ending pipeline")
        global_pipeline.set_state(Gst.State.NULL)

        mainloop.quit()
        print("exiting......")
        pass


def bus_call(bus, message, pipeline):
    t = message.type
    if t == Gst.MessageType.EOS:
        print("pipeline ended")
        pipeline.set_state(Gst.State.NULL)
        sys.exit()
    elif t == Gst.MessageType.ERROR:
        err, dbg = message.parse_error()
        print("ERROR:", message.src.get_name(), ":", err.message)
        print("error {}".format(message))
        pipeline.set_state(Gst.State.NULL)
        sys.exit()
    else:
        pass
    return True

def frame_callback(frame: VideoFrame):
    event_list = None
    
    if True:
        for i, detection in enumerate(frame.regions()):
            #print("number of tensors: ", len(detection.tensors()), " label: ", detection.label(), " roi_type: ", detection.meta().get_roi_type())
            # , " object_id : ", detection.object_id()
            for j, tensor in enumerate(detection.tensors()):
                if "detection" in tensor.name():
                    bbbox = (tensor["x_min"], tensor["y_min"], tensor["x_max"], tensor["y_max"])
                    print(i, detection.meta().get_roi_type(), bbbox, tensor["confidence"])
                elif "object_id" in tensor.name():
                    print(i, tensor["id"])
                elif "ocr" in tensor.name():
                    print(i, "MONOTOSH: ", tensor)
                else:
                    print(tensor.name())
        if event_list is not None:
            #event publish logic
            #with frame.data() as mat:
            #    cv2.imwrite("dump.jpg", mat)
            pass



def pad_probe_callback(pad, info):
    with util.GST_PAD_PROBE_INFO_BUFFER(info) as buffer:
        caps = pad.get_current_caps()
        frame = VideoFrame(buffer, caps=caps)
        frame_callback(frame)

    return Gst.PadProbeReturn.OK


def set_callbacks(pipeline):
    gvawatermark = pipeline.get_by_name("gvawatermark")
    pad = gvawatermark.get_static_pad("src")
    pad.add_probe(Gst.PadProbeType.BUFFER, pad_probe_callback)

    bus = pipeline.get_bus()
    bus.add_signal_watch()
    bus.connect("message", bus_call, pipeline)


if __name__ == '__main__':
    Gst.init(sys.argv)
    gst_launch_string = create_launch_string()
    print(gst_launch_string)
    global_pipeline = Gst.parse_launch(gst_launch_string)

    set_callbacks(global_pipeline)

    global_pipeline.set_state(Gst.State.PLAYING)

    gobject_mainloop()

    print("Exiting")