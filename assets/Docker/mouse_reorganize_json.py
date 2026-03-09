#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import json
import re



def _build_arg_parser():
    p = argparse.ArgumentParser(
        description="Reorganize metrics by ROI from a JSON file." )
    p.add_argument('in_json',
                         help='Input file name, in json format.')
    p.add_argument('out_json',
                   help='Output image path.')
    return p

def main():
    parser = _build_arg_parser()
    args = parser.parse_args()
    
    with open(args.in_json, "r") as f:
        data = json.load(f)

    new_data = {}

    for full_key, roi_dict in data.items():
        match = re.search(r'^([^_]+)__([a-z]+)', full_key)
        if not match:
            continue
        
        metric = match.group(2)
        print(f"Processing metric: {metric}")

        for roi_name, values in roi_dict.items():
            if roi_name not in new_data:
                new_data[roi_name] = {}
            
            new_data[roi_name][metric] = values
        for roi_name, values in roi_dict.items():
            if "mean" not in values or "std" not in values:
                continue

            if roi_name not in new_data:
                new_data[roi_name] = {}
            new_data[roi_name][metric] = {
                "ROI-idx": values["ROI-idx"],
                "ROI-name": values["ROI-name"],
                "max": values["max"],
                "mean": values["mean"],
                "nb-vx-roi": values["nb-vx-roi"],
                "nb-vx-seed": values["nb-vx-seed"],
                "std": values["std"]
            }
        
    with open(args.out_json, "w") as f:
        json.dump(new_data, f, indent=4)

if __name__ == "__main__":
    main()
