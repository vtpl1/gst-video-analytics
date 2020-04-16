/*******************************************************************************
 * Copyright (C) 2018-2019 Intel Corporation
 *
 * SPDX-License-Identifier: MIT
 ******************************************************************************/

#include <gst/base/gstbasetransform.h>
#include <gst/gst.h>
#include <gst/video/video.h>

#include "config.h"

#include "gstgvadetect.h"
#include "gva_caps.h"
#include "post_processors.h"
#include "pre_processors.h"

#define ELEMENT_LONG_NAME "Object detection (generates GstVideoRegionOfInterestMeta)"
#define ELEMENT_DESCRIPTION ELEMENT_LONG_NAME

enum {
    PROP_0,
    PROP_THRESHOLD,
    PROP_IS_FULL_FRAME,
    PROP_OBJECT_CLASS

};

#define DEFALUT_MIN_THRESHOLD 0.
#define DEFALUT_MAX_THRESHOLD 1.
#define DEFALUT_THRESHOLD 0.5
#define DEFAULT_IS_FULL_FRAME TRUE
#define DEFAULT_OBJECT_CLASS ""

GST_DEBUG_CATEGORY_STATIC(gst_gva_detect_debug_category);
#define GST_CAT_DEFAULT gst_gva_detect_debug_category

G_DEFINE_TYPE_WITH_CODE(GstGvaDetect, gst_gva_detect, GST_TYPE_GVA_BASE_INFERENCE,
                        GST_DEBUG_CATEGORY_INIT(gst_gva_detect_debug_category, "gvadetect", 0,
                                                "debug category for gvadetect element"));

void gst_gva_detect_set_property(GObject *object, guint property_id, const GValue *value, GParamSpec *pspec) {
    GstGvaDetect *gvadetect = (GstGvaDetect *)(object);

    GST_DEBUG_OBJECT(gvadetect, "set_property");

    switch (property_id) {
    case PROP_THRESHOLD:
        gvadetect->threshold = g_value_get_float(value);
        break;
    case PROP_IS_FULL_FRAME:
        gvadetect->base_inference.is_full_frame = g_value_get_boolean(value);
        break;
    case PROP_OBJECT_CLASS:
        gvadetect->object_class = g_value_dup_string(value);
        break;
    default:
        G_OBJECT_WARN_INVALID_PROPERTY_ID(object, property_id, pspec);
        break;
    }
}

void gst_gva_detect_get_property(GObject *object, guint property_id, GValue *value, GParamSpec *pspec) {
    GstGvaDetect *gvadetect = (GstGvaDetect *)(object);

    GST_DEBUG_OBJECT(gvadetect, "get_property");

    switch (property_id) {
    case PROP_THRESHOLD:
        g_value_set_float(value, gvadetect->threshold);
        break;
    case PROP_IS_FULL_FRAME:
        g_value_set_boolean(value, gvadetect->base_inference.is_full_frame);
        break;
    case PROP_OBJECT_CLASS:
        g_value_set_string(value, gvadetect->object_class);
        break;
    default:
        G_OBJECT_WARN_INVALID_PROPERTY_ID(object, property_id, pspec);
        break;
    }
}

void gst_gva_detect_class_init(GstGvaDetectClass *klass) {
    GstElementClass *element_class = GST_ELEMENT_CLASS(klass);

    gst_element_class_add_pad_template(
        element_class, gst_pad_template_new("src", GST_PAD_SRC, GST_PAD_ALWAYS, gst_caps_from_string(GVA_CAPS)));
    gst_element_class_add_pad_template(
        element_class, gst_pad_template_new("sink", GST_PAD_SINK, GST_PAD_ALWAYS, gst_caps_from_string(GVA_CAPS)));

    gst_element_class_set_static_metadata(element_class, ELEMENT_LONG_NAME, "Video", ELEMENT_DESCRIPTION,
                                          "Intel Corporation");

    GObjectClass *gobject_class = G_OBJECT_CLASS(klass);
    gobject_class->set_property = gst_gva_detect_set_property;
    gobject_class->get_property = gst_gva_detect_get_property;
    
    g_object_class_install_property(
        gobject_class, PROP_THRESHOLD,
        g_param_spec_float("threshold", "Threshold",
                           "Threshold for detection results. Only regions of interest "
                           "with confidence values above the threshold will be added to the frame",
                           DEFALUT_MIN_THRESHOLD, DEFALUT_MAX_THRESHOLD, DEFALUT_THRESHOLD,
                           (GParamFlags)(G_PARAM_READWRITE | G_PARAM_STATIC_STRINGS)));
    g_object_class_install_property(
        gobject_class, PROP_IS_FULL_FRAME,
        g_param_spec_boolean("is-full-frame", 
                            "Process full frame", "Process on full frame, must be TRUE for first detector and FALSE for consecutive detectors",
                            DEFAULT_IS_FULL_FRAME, G_PARAM_READWRITE | G_PARAM_STATIC_STRINGS));
    g_object_class_install_property(
        gobject_class, PROP_OBJECT_CLASS,
        g_param_spec_string("object-class", "ObjectClass", "Object class",
                            DEFAULT_OBJECT_CLASS,
                            (GParamFlags)(G_PARAM_READWRITE | G_PARAM_STATIC_STRINGS)));

}

void gst_gva_detect_init(GstGvaDetect *gvadetect) {
    GST_DEBUG_OBJECT(gvadetect, "gst_gva_detect_init");
    GST_DEBUG_OBJECT(gvadetect, "%s", GST_ELEMENT_NAME(GST_ELEMENT(gvadetect)));

    gvadetect->threshold = DEFALUT_THRESHOLD;
    gvadetect->base_inference.post_proc = EXTRACT_DETECTION_RESULTS;
    gvadetect->base_inference.is_full_frame = DEFAULT_IS_FULL_FRAME;
    gvadetect->object_class = g_strdup(DEFAULT_OBJECT_CLASS);
    gvadetect->base_inference.get_roi_pre_proc = INPUT_PRE_PROCESS_DETECTION;
    gvadetect->base_inference.post_proc = EXTRACT_DETECTION_RESULTS;
    gvadetect->base_inference.is_roi_detection_needed = IS_ROI_DETECTION_NEEDED;
}

void gst_gva_detect_cleanup(GstGvaDetect *gvadetect) {
    if (gvadetect == NULL)
        return;

    GST_DEBUG_OBJECT(gvadetect, "gst_gva_detect_cleanup");

    //release_classification_history(gvadetect->classification_history);

    g_free(gvadetect->object_class);
    gvadetect->object_class = NULL;
}

void gst_gva_detect_finalize(GObject *object) {
    GstGvaDetect *gvadetect = GST_GVA_DETECT(object);

    GST_DEBUG_OBJECT(gvadetect, "finalize");

    gst_gva_detect_cleanup(gvadetect);

    G_OBJECT_CLASS(gst_gva_detect_parent_class)->finalize(object);
}