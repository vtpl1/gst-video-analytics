#!/usr/bin/python3
# ==============================================================================
# Copyright (C) 2018-2019 Intel Corporation
#
# SPDX-License-Identifier: MIT
# ==============================================================================

import gstgva
from gi.repository import Gst, GstVideo
from argparse import ArgumentParser
import sys

import ssd_object_detection
import age_gender_classification

parser = ArgumentParser(add_help=False)
_args = parser.add_argument_group('Options')
_args.add_argument("-i", "--input", help="Required. Path to input video file",
                   required=True, type=str)
_args.add_argument("-d", "--detection_model", help="Required. Path to an .xml file with object detection model",
                   required=True, type=str)
_args.add_argument("-c", "--classification_model",
                   help="Required. Path to an .xml file with object classification model",
                   required=True, type=str)


def detect_postproc_callback(pad, info):
    with gstgva.util.GST_PAD_PROBE_INFO_BUFFER(info) as buffer:
        caps = pad.get_current_caps()
        frame = gstgva.VideoFrame(buffer, caps)
        ssd_object_detection.process_frame(frame)
    return Gst.PadProbeReturn.OK


def classify_postproc_callback(pad, info):
    with gstgva.util.GST_PAD_PROBE_INFO_BUFFER(info) as buffer:
        caps = pad.get_current_caps()
        frame = gstgva.VideoFrame(buffer, caps)
        age_gender_classification.process_frame(frame)
    return Gst.PadProbeReturn.OK


def main():
    args = parser.parse_args()

    # init GStreamer
    Gst.init(None)

    # build pipeline using parse_launch
    pipeline_str = "filesrc location={} ! decodebin ! videoconvert ! " \
        "gvainference name=gvainference model={} ! queue ! " \
        "gvaclassify name=gvaclassify model={} ! queue ! " \
        "gvawatermark ! videoconvert ! fpsdisplaysink video-sink=xvimagesink sync=false".format(
            args.input, args.detection_model, args.classification_model)
    pipeline = Gst.parse_launch(pipeline_str)

    # set callbacks
    gvainference = pipeline.get_by_name("gvainference")
    if gvainference:
        pad = gvainference.get_static_pad("src")
        pad.add_probe(Gst.PadProbeType.BUFFER, detect_postproc_callback)
    gvaclassify = pipeline.get_by_name("gvaclassify")
    if gvaclassify:
        pad = gvaclassify.get_static_pad("src")
        pad.add_probe(Gst.PadProbeType.BUFFER, classify_postproc_callback)

    # start pipeline
    pipeline.set_state(Gst.State.PLAYING)

    # wait until EOS or error
    bus = pipeline.get_bus()
    msg = bus.timed_pop_filtered(Gst.CLOCK_TIME_NONE, Gst.MessageType.ERROR | Gst.MessageType.EOS)

    # free pipeline
    pipeline.set_state(Gst.State.NULL)


if __name__ == '__main__':
    sys.exit(main() or 0)
