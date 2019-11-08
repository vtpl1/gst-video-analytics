# ==============================================================================
# Copyright (C) 2018-2019 Intel Corporation
#
# SPDX-License-Identifier: MIT
# ==============================================================================

import gstgva
from gi.repository import Gst, GstVideo

DETECT_THRESHOLD = 0.5
OBJECT_LABEL = "face"


def process_frame(frame, threshold=DETECT_THRESHOLD, label=OBJECT_LABEL):
    width = frame.width
    height = frame.height

    for tensor in frame.tensors():
        dims = tensor.dims()
        data = tensor.data()
        object_size = dims[-1]
        for i in range(dims[-2]):
            image_id = data[i * object_size + 0]
            confidence = data[i * object_size + 2]
            x_min = int(data[i * object_size + 3] * width + 0.5)
            y_min = int(data[i * object_size + 4] * height + 0.5)
            x_max = int(data[i * object_size + 5] * width + 0.5)
            y_max = int(data[i * object_size + 6] * height + 0.5)

            if image_id != 0:
                break
            if confidence < threshold:
                continue
            if x_min < 0:
                x_min = 0
            if y_min < 0:
                y_min = 0
            if x_max > width:
                x_max = width
            if y_max > height:
                y_max = height

            GstVideo.buffer_add_video_region_of_interest_meta(
                frame.buffer, label, x_min, y_min, x_max - x_min, y_max - y_min)

    return True
