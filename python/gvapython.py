# ==============================================================================
# Copyright (C) 2018-2019 Intel Corporation
#
# SPDX-License-Identifier: MIT
# ==============================================================================

import gi

gi.require_version('Gst', '1.0')
gi.require_version('GstBase', '1.0')

from gi.repository import Gst, GObject, GLib, GstBase
import os
import json
import importlib
import gstgva
import sys
import logging


Gst.init(None)


class CustomTransform(GstBase.BaseTransform):

    DEFAULT_MODULE = None
    DEFAULT_FUNCTION = "process_frame"
    DEFAULT_CLASS_NAME = None
    DEFAULT_ARGS = "{}"
    CAPS_STRING = "ANY"
    GST_PLUGIN_NAME = 'gvapython'
    DEFAULT_PACKAGE = None
    LONG_NAME = "Process buffer with user defined function."

    GST_BASE_TRANSFORM_FLOW_DROPPED = Gst.FlowReturn.CUSTOM_SUCCESS

    __gstmetadata__ = (LONG_NAME,
                       "Transform",
                       LONG_NAME,
                       "Intel Corporation")

    __gsttemplates__ = (Gst.PadTemplate.new("src",
                                            Gst.PadDirection.SRC,
                                            Gst.PadPresence.ALWAYS,
                                            Gst.Caps.from_string(CAPS_STRING)),
                        Gst.PadTemplate.new("sink",
                                            Gst.PadDirection.SINK,
                                            Gst.PadPresence.ALWAYS,
                                            Gst.Caps.from_string(CAPS_STRING)))

    __gstmeta__ = __gstmetadata__

    __gproperties__ = {
        "module": (str,
                   "Module for user defined function.",
                   "Module for user defined function",
                   DEFAULT_MODULE,
                   GObject.ParamFlags.READWRITE | GObject.PARAM_STATIC_STRINGS),
        "function": (str,
                     "Funcion name",
                     "Function name",
                     DEFAULT_FUNCTION,
                     GObject.ParamFlags.READWRITE | GObject.PARAM_STATIC_STRINGS),
        "class": (str,
                  "Class name for user defined function.",
                  "Class name for user defined function.",
                  DEFAULT_CLASS_NAME,
                  GObject.ParamFlags.READWRITE | GObject.PARAM_STATIC_STRINGS),
        "package": (str,
                    "Package for user defined function.",
                    "Package for user defined function.",
                    DEFAULT_PACKAGE,
                    GObject.ParamFlags.READWRITE | GObject.PARAM_STATIC_STRINGS),

        "args": (str,
                 "JSON object containing arguments to be passed to class on initialization. If specified multiple times arguments will be combined into single object.",
                 "JSON object containing arguments to be passed to class on initialization. If specified multiple times arguments will be combined into single object.",
                 DEFAULT_ARGS,
                 GObject.ParamFlags.READWRITE | GObject.PARAM_STATIC_STRINGS),

    }

    def _load_function(self):

        filename, extension = os.path.splitext(self.module_name)
        if (extension == '.py'):
            self.module_name = filename

        head, tail = os.path.split(self.module_name)
        if (head):
            sys.path.append(os.path.abspath(head))
            self.module_name = tail

        if (self.package_name):

            head, tail = os.path.split(self.package_name)
            if (head):
                sys.path.append(os.path.abspath(head))
                self.package_name = tail
            self.module_name = ".{}".format(self.module_name)

        lib = importlib.import_module(
            self.module_name,
            package=self.package_name)

        if (self.class_name):
            _class = getattr(lib, self.class_name)
            _function_instance = _class(**self.args)
            self._function = getattr(_function_instance, self.function_name)
            self._function_args = {}
        else:
            self._function_args = self.args
            self._function = getattr(lib, self.function_name)

    def __init__(self):
        super(CustomTransform, self).__init__()
        self.class_name = CustomTransform.DEFAULT_CLASS_NAME
        self.args = json.loads(CustomTransform.DEFAULT_ARGS)
        self.package_name = CustomTransform.DEFAULT_PACKAGE
        self.function_name = CustomTransform.DEFAULT_FUNCTION
        self.module_name = CustomTransform.DEFAULT_MODULE
        self._ref = self

    def do_set_property(self, prop, value):
        if (prop.name == "args"):
            self.args.update(json.loads(value))

        setattr(self, prop.name+'_name', value)

    def do_get_property(self, prop):

        name = prop.name
        if (prop.name != "args"):
            name = name+"_name"

        return getattr(self, name)

    def do_start(self):
        try:
            self._load_function()
        except Exception as error:
            self.post_message(Gst.Message.new_error(self, GLib.Error(), str(error)))
            return False

        return True

    def do_stop(self):
        self._ref = None
        return True

    def do_transform_ip(self, buffer):
        gst_result = Gst.FlowReturn.OK
        function_result = True
        if self._function:
            with gstgva.util.TRANSFORM_IP_BUFFER(buffer):
                caps = self.sinkpad.get_current_caps()
                frame = gstgva.Frame(buffer, caps)
                try:
                    function_result = self._function(frame, **self._function_args)
                except Exception as error:
                    self.post_message(Gst.Message.new_error(self, GLib.Error(), str(error)))
                    gst_result = Gst.FlowReturn.ERROR
        if not function_result:
            gst_result = CustomTransform.GST_BASE_TRANSFORM_FLOW_DROPPED

        return gst_result


def register(class_info):

    def init(plugin, plugin_impl, plugin_name):
        type_to_register = GObject.type_register(plugin_impl)
        return Gst.Element.register(plugin, plugin_name, 0, type_to_register)

    version = '1.0'
    gstlicense = 'MIT/X11'
    origin = 'Intel'
    source = class_info.__gstmeta__[1]
    package = class_info.__gstmeta__[0]
    name = class_info.__gstmeta__[0]
    description = class_info.__gstmeta__[2]
    def init_function(plugin): return init(plugin, class_info, name)

    if not Gst.Plugin.register_static(Gst.VERSION_MAJOR, Gst.VERSION_MINOR,
                                      name, description,
                                      init_function, version, gstlicense,
                                      source, package, origin):
        raise ImportError("Plugin {} not registered".format(name))
    return True


register(CustomTransform)

GObject.type_register(CustomTransform)
__gstelementfactory__ = (CustomTransform.GST_PLUGIN_NAME,
                         Gst.Rank.NONE, CustomTransform)
