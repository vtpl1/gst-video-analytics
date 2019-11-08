# ==============================================================================
# Copyright (C) 2018-2019 Intel Corporation
#
# SPDX-License-Identifier: MIT
# ==============================================================================

from enum import Enum
import ctypes
import numpy
from gi.repository import GObject

from .util import libgst, libgstva

GVA_TENSOR_MAX_RANK = 8


class TensorMeta(ctypes.Structure):
    _fields_ = [('_meta_flags', ctypes.c_int),
                ('_info', ctypes.c_void_p),
                ('_precision', ctypes.c_int),
                ('_rank', ctypes.c_uint),
                ('_dims', ctypes.c_size_t*GVA_TENSOR_MAX_RANK),
                ('_layout', ctypes.c_int),
                ('_layer_name', ctypes.c_char_p),
                ('_model_name', ctypes.c_char_p),
                ('_data', ctypes.POINTER(ctypes.c_byte)),
                ('_total_bytes', ctypes.c_size_t),
                ('_element_id', ctypes.c_char_p),
                ]

    class PRECISION(Enum):
        UNSPECIFIED = 255
        FP32 = 10
        U8 = 40

    class LAYOUT(Enum):
        ANY = 0
        NCHW = 1
        NHWC = 2

    def rank(self):
        return self._rank

    def total_bytes(self):
        return self._total_bytes

    def element_id(self):
        return self._element_id.decode('utf-8')

    def layer_name(self):
        return self._layer_name.decode('utf-8')

    def model_name(self):
        return self._model_name.decode('utf-8')

    def dims(self):
        return [self._dims[i] for i in range(self._rank)]

    def data(self):
        precision = self.precision()
        if (precision == TensorMeta.PRECISION.FP32):
            view = numpy.float32
        elif (precision == TensorMeta.PRECISION.U8):
            view = numpy.uint8

        array_type = ctypes.c_ubyte * self._total_bytes
        address = ctypes.addressof(self._data.contents)

        return numpy.ctypeslib.as_array(array_type.from_address(address)).view(dtype=view)

    def layout(self):
        try:
            return TensorMeta.LAYOUT(self._layout)
        except:
            return TensorMeta.LAYOUT.ANY

    def precision(self):
        try:
            return TensorMeta.PRECISION(self._precision)
        except:
            return TensoMeta.PRECISION.UNSPECIFIED

    def set_fields(self,
                   precision,
                   rank,
                   dims,
                   layout,
                   layer_name,
                   model_name,
                   data,
                   total_bytes,
                   element_id):

        dims_array = (ctypes.c_size_t*GVA_TENSOR_MAX_RANK)(*dims)

        return libgstva.gva_set_tensor(self,
                                       precision.value,
                                       rank,
                                       dims_array,
                                       layout.value,
                                       layer_name.encode('utf-8'),
                                       model_name.encode('utf-8'),
                                       ctypes.c_void_p(data.ctypes.data),
                                       total_bytes,
                                       element_id.encode('utf-8'))

    @classmethod
    def remove_tensor_meta(cls, buffer, tensor):
        return libgst.gst_buffer_remove_meta(hash(buffer),
                                             ctypes.byref(tensor))

    @classmethod
    def add_tensor_meta(cls,
                        buffer,
                        precision,
                        rank,
                        dims,
                        layout,
                        layer_name,
                        model_name,
                        data,
                        total_bytes,
                        element_id):
        try:
            value = libgst.gst_buffer_add_meta(hash(buffer),
                                               libgstva.gst_gva_tensor_meta_get_info(),
                                               None)
        except Exception as error:
            value = None

        if value is None:
            return

        meta = ctypes.cast(value, GST_GVA_TENSOR_META_POINTER).contents

        meta.set_fields(precision,
                        rank,
                        dims,
                        layout,
                        layer_name,
                        model_name,
                        data,
                        total_bytes,
                        element_id)

        return meta

    @classmethod
    def iterate(cls, buffer):
        try:
            meta_api = hash(GObject.GType.from_name("GstGVATensorMetaAPI"))
        except:
            return
        gpointer = ctypes.c_void_p()
        while True:
            try:
                value = libgst.gst_buffer_iterate_meta_filtered(hash(buffer),
                                                                ctypes.byref(gpointer),
                                                                meta_api)
            except Exception as error:
                value = None

            if value is None:
                return

            meta = ctypes.cast(value, GST_GVA_TENSOR_META_POINTER).contents

            yield meta


GST_GVA_TENSOR_META_POINTER = ctypes.POINTER(TensorMeta)

libgstva.gst_gva_tensor_meta_get_info.argtypes = None
libgstva.gst_gva_tensor_meta_get_info.restype = ctypes.c_void_p

libgstva.gva_set_tensor.argtypes = [GST_GVA_TENSOR_META_POINTER,
                                    ctypes.c_int,
                                    ctypes.c_uint,
                                    ctypes.c_size_t*GVA_TENSOR_MAX_RANK,
                                    ctypes.c_int,
                                    ctypes.c_char_p,
                                    ctypes.c_char_p,
                                    ctypes.c_void_p,
                                    ctypes.c_size_t,
                                    ctypes.c_char_p]

libgstva.gva_set_tensor.restype = None
