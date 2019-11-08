# ==============================================================================
# Copyright (C) 2018-2019 Intel Corporation
#
# SPDX-License-Identifier: MIT
# ==============================================================================

import ctypes
import gi

gi.require_version('Gst', '1.0')
gi.require_version('GstVideo', '1.0')
gi.require_version('GLib', '2.0')

from gi.repository import Gst, GObject, GstVideo, GLib

from .util import libgst, libgstva


class JSONMeta(ctypes.Structure):
    _fields_ = [('_meta_flags', ctypes.c_int),
                ('_info', ctypes.c_void_p),
                ('_message', ctypes.c_char_p)
                ]

    def get_message(self):
        return self._message.decode('utf-8')

    def set_message(self, message):
        return libgstva.set_json_message(self, message.encode('utf-8'))

    @classmethod
    def get_json_message(cls, meta):
        return libgstva.get_json_message(hash(meta)).decode('utf-8')

    @classmethod
    def get_json_meta(cls, buffer):
        return ctypes.cast(hash(buffer.get_meta("GstGVAJSONMetaAPI")), GST_GVA_JSON_META_POINTER).contents

    @classmethod
    def remove_json_meta(cls, buffer, meta):
        return libgst.gst_buffer_remove_meta(hash(buffer),
                                             ctypes.byref(meta))

    @classmethod
    def add_json_meta(cls, buffer, message):
        try:
            value = libgst.gst_buffer_add_meta(hash(buffer),
                                               libgstva.gst_gva_json_meta_get_info(),
                                               None)
        except Exception as error:
            value = None

        if value is None:
            return

        meta = ctypes.cast(value, GST_GVA_JSON_META_POINTER).contents
        meta.set_message(message)

        return meta

    @classmethod
    def iterate(cls, buffer):
        try:
            meta_api = hash(GObject.GType.from_name("GstGVAJSONMetaAPI"))
        except:
            return
        gpointer = ctypes.c_void_p()
        while(True):
            try:
                value = libgst.gst_buffer_iterate_meta_filtered(hash(buffer),
                                                                ctypes.byref(gpointer),
                                                                meta_api)
            except Exception as error:
                value = None

            if value is None:
                return

            meta = ctypes.cast(value, GST_GVA_JSON_META_POINTER).contents

            yield meta


GST_GVA_JSON_META_POINTER = ctypes.POINTER(JSONMeta)
libgstva.get_json_message.argtypes = [ctypes.c_void_p]
libgstva.get_json_message.restype = ctypes.c_char_p
libgstva.set_json_message.argtypes = [GST_GVA_JSON_META_POINTER, ctypes.c_char_p]
libgstva.set_json_message.restype = None
libgstva.gst_gva_json_meta_get_info.argtypes = None
libgstva.gst_gva_json_meta_get_info.restype = ctypes.c_void_p
