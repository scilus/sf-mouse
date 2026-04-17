#! /usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Extract the brain mask from an anatomical image using ants and antspynet.
"""

import argparse
import os

import ants
import antspynet
import argparse
from antspynet import mouse_brain_extraction

parser = argparse.ArgumentParser(description="")
parser.add_argument('input_anat', type=str, help="Path to the anatomical image.")
parser.add_argument('output_mask', type=str, help="Path to the output mask file.")

args = parser.parse_args()

filename_input=args.input_anat
filename_output=args.output_mask

mri_image = ants.image_read(filename_input)

output = mouse_brain_extraction(mri_image,modality="t2")
ants.image_write(output,filename_output)


