# ==============================================================================
# Copyright (C) 2018-2019 Intel Corporation
#
# SPDX-License-Identifier: MIT
# ==============================================================================

import cv2
import json
import numpy
from collections import Counter
import time
import gstgva


class BottleCount:

    def __init__(self, redact_person=True):
        self.redact_person = redact_person
        self.item_count = Counter()

    def remove_regions(self, frame):
        for region in list(frame.regions()):
            frame.remove_region(region)

    def process_frame(self, frame):
        timestamp = int(round(time.time()*1000))
        events = []

        new_counts = Counter()

        for detection in frame.regions():
            new_counts[detection.get_roi_type()] += 1

        for key, count in new_counts.items():
            if (key in self.item_count):
                if (count > self.item_count[key]):
                    for x in range(0, count-self.item_count[key]):
                        events.append({'event_time': timestamp,
                                       'roi_action': 'ENTER',
                                       'object_id': key})
                elif (count < self.item_count[key]):
                    for x in range(0, self.item_count[key]-count):
                        events.append({'event_time': timestamp,
                                       'roi_action': 'DEPART',
                                       'object_id': key})
            else:
                for x in range(0, count):
                    events.append({'event_time': timestamp,
                                   'roi_action': 'ENTER',
                                   'object_id': key})
        for key, count in self.item_count.items():
            if (key not in new_counts):
                for x in range(0, count):
                    events.append({'event_time': timestamp,
                                   'roi_action': 'DEPART',
                                   'object_id': key})

        if (events):
            frame.add_message(json.dumps(events))

        self.item_count = new_counts

        if (self.item_count['bottle'] <= 1):
            frame.add_region("LOW COUNT", 0, 0, 0, 0)
        else:
            frame.add_region("Bottle Count: " + str(self.item_count['bottle']), 0, 0, 0, 0)

        if (self.item_count['person'] > 0) and (self.redact_person):
            with frame.data() as contents:
                contents[:] = 0
            self.remove_regions(frame)
            frame.add_region("PERSON DETECTED FRAME DELETED", 0, 0, 0, 0)

        return True
