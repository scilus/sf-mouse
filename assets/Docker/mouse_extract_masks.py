#! /usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Extract csv files containing only the rows that match the given labels.
Extract a txt file containing the IDS of the labels.
"""

import argparse
import os
import logging

import pandas as pd

from scilpy.io.utils import (add_overwrite_arg, add_verbose_arg,
                             assert_inputs_exist,
                             assert_output_dirs_exist_and_empty)


def _build_arg_parser():
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawTextHelpFormatter)

    p.add_argument('in_atlas',
                   help='Path to the ANO registered atlas.')

    p.add_argument('in_labels', nargs='+',
                   help='Labels to extract (from any Level column).')

    p.add_argument('out_folder',
                   help='Output folder where to save the masks and csv files.')

    p.add_argument('--merge', action='store_true',
                   help='Merge the left and right into a single CSV file')

    add_verbose_arg(p)
    add_overwrite_arg(p)
    return p


def main():
    parser = _build_arg_parser()
    args = parser.parse_args()
    logging.getLogger().setLevel(logging.getLevelName(args.verbose))

    assert_inputs_exist(parser, args.in_atlas)
    assert_output_dirs_exist_and_empty(parser, args, args.out_folder)

    df = pd.read_csv('/ANO_taxonomy_EC_V4.csv', sep=';')
    df.fillna("Empty", inplace=True)
    for curr_label in args.in_labels:
        curr_label_name = curr_label + ' '
        curr_label_found = False
        for curr_column in list(df.filter(regex='Level').columns):
            logging.info(f'Checking {curr_column}')
            if df[curr_column].str.contains(curr_label_name).sum():
                curr_label_found = True
                logging.info(f'Found {curr_label_name} in {curr_column}')
                curr_df = df[df[curr_column].str.contains(curr_label_name)]
                curr_df = curr_df.replace("Empty", "")
                if args.merge:
                    curr_df.to_csv(os.path.join(args.out_folder,
                                                f'{curr_label}.csv'),
                                   sep=';',
                                   index=False)

                    curr_ids = list(curr_df['Val_L'].values) + list(curr_df['Val_R'].values)
                    with open(os.path.join(args.out_folder, f'{curr_label}.txt'), 'w') as f:
                        f.write(" ".join(str(x) for x in curr_ids))
                else:
                    for side in ['L', 'R']:
                        dropped_column = f'Val_{"R" if side == "L" else "L"}'
                        curr_df.drop(columns=[dropped_column]).to_csv(os.path.join(args.out_folder,
                                                                                   f'{curr_label}_{side}.csv'),
                                                                      sep=';',
                                                                      index=False)
                        curr_ids = list(curr_df[f'Val_{side}'].values)
                        with open(os.path.join(args.out_folder, f'{curr_label}_{side}.txt'), 'w') as f:
                            f.write(" ".join(str(x) for x in curr_ids))
                break
        
        if not curr_label_found:
            if args.merge:
                with open(os.path.join(args.out_folder, f'{curr_label}.txt'), 'w') as f:
                    f.write("")
            else:
                for side in ['L', 'R']:
                    with open(os.path.join(args.out_folder, f'{curr_label}_{side}.txt'), 'w') as f:
                        f.write("")

if __name__ == "__main__":
    main()
