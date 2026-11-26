#!/usr/bin/env python3
"""Check anatomical mask and DWI grids before and after alignment."""

import argparse

import nibabel as nib
import numpy as np


def same_grid(first, second):
    return first.shape == second.shape and np.allclose(first.affine, second.affine, atol=1e-4, rtol=0)


def check_geometry(image, label):
    if len(image.shape) != 3:
        raise ValueError(f"{label} must be a 3D image")
    if not np.isfinite(image.affine).all() or abs(np.linalg.det(image.affine[:3, :3])) < 1e-12:
        raise ValueError(f"{label} must have a finite, non-singular affine")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("reference")
    parser.add_argument("mask")
    parser.add_argument("--anatomy")
    parser.add_argument("--require-match", action="store_true")
    args = parser.parse_args()

    reference = nib.load(args.reference)
    mask = nib.load(args.mask)
    check_geometry(reference, "Reference b0")
    check_geometry(mask, "Anatomical mask")
    values = np.asanyarray(mask.dataobj)
    if not np.isfinite(values).all() or np.any(values < 0) or not np.any(values > 0):
        raise ValueError("Anatomical mask must be finite, non-negative and nonempty")
    if args.anatomy:
        anatomy = nib.load(args.anatomy)
        check_geometry(anatomy, "Anatomical image")
        if not same_grid(anatomy, mask):
            raise ValueError("Anatomical image and mask must share a 3D grid")
    matches = same_grid(reference, mask)
    if args.require_match and not matches:
        raise ValueError("Aligned anatomical mask must share the DWI b0 grid")
    print("same" if matches else "different")


if __name__ == "__main__":
    main()
