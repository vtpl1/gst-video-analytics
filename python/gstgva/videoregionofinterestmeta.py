# ==============================================================================
# Copyright (C) 2018-2019 Intel Corporation
#
# SPDX-License-Identifier: MIT
# ==============================================================================

from enum import Enum
import ctypes
import numpy
from .util import libgst, libgobject, libgstvideo, GLIST_POINTER
import gi

gi.require_version('GstVideo', '1.0')
gi.require_version('GLib', '2.0')
gi.require_version('Gst', '1.0')

from gi.repository import GstVideo, GLib, GObject, Gst


class VideoRegionOfInterestMeta(ctypes.Structure):
    _fields_ = [
        ('_meta_flags', ctypes.c_int),
        ('_info', ctypes.c_void_p),
        ('_roi_type', ctypes.c_int),
        ('id', ctypes.c_int),
        ('parent_id', ctypes.c_int),
        ('x', ctypes.c_int),
        ('y', ctypes.c_int),
        ('w', ctypes.c_int),
        ('h', ctypes.c_int),
        ('_params', GLIST_POINTER)
    ]

    def get_roi_type(self):
        return GLib.quark_to_string(self._roi_type)

    def set_roi_type(self, new_type):
        self._roi_type = GLib.quark_from_string(new_type)

    def add_tensor(self, name):
        tensor = libgst.gst_structure_new_empty(name.encode('utf-8'))
        libgstvideo.gst_video_region_of_interest_meta_add_param(self, tensor)
        return Tensor(tensor)

    def remove_tensor(self, tensor):
        libgobject.g_list_remove(self._params, tensor._structure)

    def get_tensor(self, name):
        param = libgstvideo.gst_video_region_of_interest_meta_get_param(self, name.encode('utf-8'))
        if (param):
            return Tensor(param)

    def tensors(self):
        param = self._params
        while param:
            yield Tensor(param.contents.data)
            param = param.contents.next

    @classmethod
    def remove_video_region_of_interest_meta(cls, buffer, meta):
        return libgst.gst_buffer_remove_meta(hash(buffer),
                                             ctypes.byref(meta))

    @classmethod
    def add_video_region_of_interest_meta(cls, buffer, label, x, y, width, height):
        value = GstVideo.buffer_add_video_region_of_interest_meta(buffer,
                                                                  label,
                                                                  x,
                                                                  y,
                                                                  width,
                                                                  height)
        return ctypes.cast(hash(value), ctypes.POINTER(VideoRegionOfInterestMeta)).contents

    @classmethod
    def iterate(cls, buffer):
        try:
            meta_api = hash(GObject.GType.from_name("GstVideoRegionOfInterestMetaAPI"))
        except:
            return
        gpointer = ctypes.c_void_p()
        while True:
            try:
                value = libgst.gst_buffer_iterate_meta_filtered(hash(buffer),
                                                                ctypes.byref(gpointer),
                                                                meta_api)
            except:
                value = None
            if value is None:
                return
            meta = ctypes.cast(value, ctypes.POINTER(VideoRegionOfInterestMeta)).contents
            yield meta


VIDEO_REGION_OF_INTEREST_POINTER = ctypes.POINTER(VideoRegionOfInterestMeta)
libgstvideo.gst_video_region_of_interest_meta_get_param.argtypes = [VIDEO_REGION_OF_INTEREST_POINTER,
                                                                    ctypes.c_char_p]
libgstvideo.gst_video_region_of_interest_meta_get_param.restype = ctypes.c_void_p

libgstvideo.gst_video_region_of_interest_meta_add_param.argtypes = [VIDEO_REGION_OF_INTEREST_POINTER,
                                                                    ctypes.c_void_p]
libgstvideo.gst_video_region_of_interest_meta_add_param.restype = None


class Tensor:
    class PRECISION(Enum):
        ANY = 0
        FP32 = 10
        U8 = 40

    class LAYOUT(Enum):
        ANY = 0
        NCHW = 1
        NHWC = 2
        NC = 193

    def __init__(self, structure):
        self._structure = structure

    def label(self):
        return self["label"]

    def label_id(self):
        return self["label_id"]

    def object_id(self):
        return self["object_id"]

    def model_name(self):
        return self["model_name"]

    def format(self):
        return self["format"]

    def confidence(self):
        return self["confidence"]

    def layer_name(self):
        return self["layer_name"]

    def name(self):
        name = libgst.gst_structure_get_name(self._structure)
        if (name):
            return name.decode('utf-8')
        return None

    def set_name(self, name):
        return libgst.gst_structure_set_name(self._structure, name.encode('utf-8'))

    def data(self):
        precision = self.precision()
        if (precision == Tensor.PRECISION.FP32):
            view = numpy.float32
        elif (precision == Tensor.PRECISION.U8):
            view = numpy.uint8
        else:
            return None
        gvalue = libgst.gst_structure_get_value(self._structure, 'data_buffer'.encode('utf-8'))
        if (gvalue):
            gvariant = libgobject.g_value_get_variant(gvalue)
            nbytes = ctypes.c_size_t()
            data_ptr = libgobject.g_variant_get_fixed_array(gvariant, ctypes.byref(nbytes), 1)
            array_type = ctypes.c_ubyte * nbytes.value
            return numpy.ctypeslib.as_array(array_type.from_address(data_ptr)).view(dtype=view)
        return None

    def layout(self):
        try:
            return Tensor.LAYOUT(self["layout"])
        except:
            return Tensor.LAYOUT.ANY

    def precision(self):
        try:
            return Tensor.PRECISION(self["precision"])
        except:
            return Tensor.PRECISION.ANY

    def set_label(self, label):
        self['label'] = label

    def __setitem__(self, key, item):
        gvalue = GObject.Value()
        if isinstance(item, str):
            gvalue.init(GObject.TYPE_STRING)
            gvalue.set_string(item)
        elif isinstance(item, int):
            gvalue.init(GObject.TYPE_INT)
            gvalue.set_int(item)
        elif isinstance(item, float):
            gvalue.init(GObject.TYPE_INT)
            gvalue.set_double(item)
        else:
            raise ValueError
        libgst.gst_structure_set_value(self._structure, key.encode('utf-8'), hash(gvalue))

    def __getitem__(self, key):
        key = key.encode('utf-8')
        gtype = libgst.gst_structure_get_field_type(self._structure, key)
        if gtype == hash(GObject.TYPE_STRING):
            res = libgst.gst_structure_get_string(self._structure, key)
            return res.decode("utf-8") if res else None
        elif gtype == hash(GObject.TYPE_INT):
            value = ctypes.c_int()
            res = libgst.gst_structure_get_int(self._structure, key, ctypes.byref(value))
            return value.value if res else None
        elif gtype == hash(GObject.TYPE_DOUBLE):
            value = ctypes.c_double()
            res = libgst.gst_structure_get_double(self._structure, key, ctypes.byref(value))
            return value.value if res else None
        else:
            return None

    def __len__(self):
        return libgst.gst_structure_n_fields(self._structure)

    def keys(self):
        return [libgst.gst_structure_nth_field_name(self._structure, i).decode("utf-8") for i in range(self.__len__())]

    def __iter__(self):
        for key in self.keys():
            yield key, self.__getitem__(key)

    def __repr__(self):
        return repr(dict(self))

    def __delitem__(self, key):
        libgst.gst_structure_remove_field(self._structure, key.encode('utf-8'))
