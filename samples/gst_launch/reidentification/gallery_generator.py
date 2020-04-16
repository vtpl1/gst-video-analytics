#!/bin/python3
# ==============================================================================
# Copyright (C) 2018-2020 Intel Corporation
#
# SPDX-License-Identifier: MIT
# ==============================================================================

import json
import argparse
import os
import shutil
import subprocess
import re
import fnmatch
import shlex
from sys import version_info

description = """
Sample tool to generate feature database by image folder using gstreamer pipeline.

The name of the label is chosen as follows:
1) filename - if image is in the root of image folder
2) folder name - if image is in the subfolder
"""

class Processor(object):
    def __init__(self,argument):
        self.output_file = argument
    def process_frame(self,video_frame):
        for region in video_frame.regions():
            for tensor in region.tensors():
                if tensor.has_field('format'):
                    if tensor['format'] == "cosine_distance":
                        with open(self.output_file, 'wb') as ofile:
                            tensor.data().tofile(ofile)

def get_input(display_text):
    if version_info.major == 3:
        return input(display_text) #nosec, use of input is safe on Python3
    return ''


def find_files(directory, pattern='*.*'):
    if not os.path.exists(directory):
        raise ValueError("Directory not found {}".format(directory))

    matches = []
    for root, _, filenames in os.walk(directory):
        for filename in filenames:
            full_path = os.path.join(root, filename)
            if fnmatch.filter([full_path], pattern):
                matches.append(os.path.join(root, filename))
    return matches


def get_models_path():
    models_path = os.getenv("MODELS_PATH", None)

    if models_path is None:
        models_path = os.getenv("INTEL_CVSDK_DIR", None)
        if models_path is not None:
            models_path = os.path.join(
                models_path, "deployment_tools", "intel_models")
            pass
        pass
    if models_path is None:
        print(
            "Warning: default models path not found by envs MODELS_PATH and INTEL_CVSDK_DIR")
        pass
    return models_path


def find_model_path(model_name, models_dir_list):
    model_path_list = []
    file_pattern = "*{}.xml".format(model_name)
    for models_dir in models_dir_list:
        if not os.path.exists(models_dir):
            continue
        model_path_list += find_files(models_dir, file_pattern)
    return model_path_list


def find_models_paths(model_names, models_dir_list):
    if not model_names:
        raise ValueError("Model names are not set")
    if not models_dir_list:
        raise ValueError("Model directories are not set")

    d = {}
    for model_name in model_names:
        d[model_name] = None
        model_path_list = find_model_path(model_name, models_dir_list)
        if not model_path_list:
            continue
        if len(model_path_list) > 1:
            print(
                "Warning: Find few models with name: {}. Take the first.".format(model_name))
        d[model_name] = model_path_list.pop(0)
    return d


pipeline_template = "gst-launch-1.0 \
        filesrc location={input_file} ! decodebin ! videoconvert ! video/x-raw,format=BGRx ! \
        gvadetect model={detection_model} pre-process-backend=opencv ! \
        gvaclassify model={landmarks_model} model-proc={landmarks_modelproc} pre-process-backend=opencv ! \
        gvaclassify model={identification_model} model-proc={identification_modelproc} pre-process-backend=opencv ! \
        gvapython module=" + os.path.realpath(__file__) + ' class=Processor arg=[\\"{output_file}\\"] ! \
        fakesink sync=false'
feature_file_regexp_template = r"^{label}_\d+.tensor$"

default_detection_model = "face-detection-adas-0001"
default_landmarks_model = "landmarks-regression-retail-0009"
default_identification_model = "face-reidentification-retail-0095"
default_models_paths = None if not get_models_path() else get_models_path().split(":")
models_paths = find_models_paths(
    [default_detection_model, default_landmarks_model, default_identification_model], default_models_paths)

default_detection_path = models_paths.get(default_detection_model)
default_identification_path = models_paths.get(default_identification_model)
default_landmarks_path = models_paths.get(default_landmarks_model)
default_identification_modelproc_path = "../../model_proc/{}.json".format(
    default_identification_model)
default_landmarks_modelproc_path = "../../model_proc/{}.json".format(
    default_landmarks_model)
default_output = os.path.curdir

KNOWN_ANSWERS = ['yes', 'y', 'Y','']


def parse_arg():
    parser = argparse.ArgumentParser(
        description=description, formatter_class=argparse.RawTextHelpFormatter)

    parser.add_argument("--source_dir", "-s", required=True,
                        help="Path to the folder with images")
    parser.add_argument(
        "--output", "-o", default=default_output, help="Path to output folder")
    parser.add_argument("--detection", "-d", default=default_detection_path,
                        help="Path to detection model xml file")
    parser.add_argument("--identification", "-i", default=default_identification_path,
                        help="Path to identification model xml file")
    parser.add_argument("--landmarks_regression", "-l", default=default_landmarks_path,
                        help="Path to landmarks-regression model xml file")
    parser.add_argument("--identification_modelproc", default=default_identification_modelproc_path,
                        help="Path to identification modelproc json file")
    parser.add_argument("--landmarks_regression_modelproc", default=default_landmarks_modelproc_path,
                        help="Path to landmarks-regression modelproc json file")

    return parser.parse_args()


if __name__ == "__main__":
    args = parse_arg()

    output_path = args.output
    gallery_folder = os.path.join(output_path, "gallery")
    features_out = os.path.join(gallery_folder, "features")
    if os.path.exists(features_out):
        answer = get_input("Gallery already exists. Want to rewrite it? [Y/n]\n")
        if answer.lower() not in KNOWN_ANSWERS:
            exit()
        shutil.rmtree(features_out)
    os.makedirs(features_out)

    gallery = []

    os.environ['LC_NUMERIC'] = 'C'
    for folder, subdir_list, file_list in os.walk(args.source_dir):
        for idx, filename in enumerate(file_list):
            label = os.path.splitext(
                filename)[0] if folder == args.source_dir else os.path.basename(folder)
            abs_path = os.path.join(os.path.abspath(folder), filename)
            pipeline = pipeline_template.format(input_file=abs_path, detection_model=args.detection,
                                                landmarks_model=args.landmarks_regression,
                                                landmarks_modelproc=args.landmarks_regression_modelproc,
                                                identification_model=args.identification,
                                                identification_modelproc=args.identification_modelproc,
                                                output_file=os.path.join(features_out,label+"_"+str(idx)+".tensor"))
            proc = subprocess.Popen(
                shlex.split(pipeline), shell=False, env=os.environ.copy())
            if proc.wait() != 0:
                print("Error while running pipeline")
                exit(-1)

            already_in_gallery = False
            for i in range(len(gallery)):
                if label == gallery[i]["name"]:
                    already_in_gallery = True
            if not already_in_gallery:
                gallery.append({'name':label})
                pass
            pass
        pass

    output_files = os.listdir(features_out)

    for i in range(len(gallery)):
        label = gallery[i]["name"]
        regexp = re.compile(feature_file_regexp_template.format(label=label))
        gallery[i]['features'] = [os.path.join(
            'features/', x) for x in output_files if regexp.match(x)]
        pass
    with open(os.path.join(gallery_folder, "gallery.json"), 'w') as f:
        json.dump(gallery, f)
        pass
    pass
