# ==============================================================================
# Copyright (C) 2018-2019 Intel Corporation
#
# SPDX-License-Identifier: MIT
# ==============================================================================

import gstgva
from gi.repository import Gst, GObject, GstVideo
import sys


def process_frame(frame):
    for region in frame.regions():
        for tensor in region.tensors():
            layer_name = tensor.layer_name()
            data = tensor.data()
            if 'age' in layer_name:
                tensor.set_label(str(int(data[0] * 100)))
            if 'gender' in tensor.model_name() and 'prob' in layer_name:
                tensor.set_label(" M " if data[1] > 0.5 else " F ")
            if 'EmoNet' in layer_name:
                emotions = ["neutral", "happy", "sad", "surprise", "anger"]
                tensor.set_label(emotions[data.index(max(data))])

    return True
