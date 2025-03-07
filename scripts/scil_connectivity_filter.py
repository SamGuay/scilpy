#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Script to facilitate filtering of connectivity matrices.
The same could be achieved through a complex sequence of
scil_connectivity_math.py.

Can be used with any connectivity matrix from
scil_connectivity_compute_matrices.py.

For example, a filtering as performed in [1] would be:
scil_connectivity_filter.py out_mask.npy
    --greater_than */sc.npy 1 0.90
    --lower_than */sim.npy 2 0.90
    --greater_than */len.npy 40 0.90 -v;

This will result in a binary mask where each node with a value of 1 represents
a node with at least 90% of the population having at least 1 streamline,
90% of the population being similar to the average (2mm) and 90% of the
population having at least 40mm of average streamlines length.

All operations are stricly > or <, there is no >= or <=.

--greater_than or --lower_than expect the same convention:
    MATRICES_LIST VALUE_THR POPULATION_PERC
It is strongly recommended (but not enforced) that the same number of
connectivity matrices is used for each condition.

This script performs an intersection of all conditions, meaning that all
conditions must be met in order to not be filtered.

If the user wants to manually handle the requirements, --keep_condition_count
can be used and manually binarized using scil_connectivity_math.py

Formerly: scil_filter_connectivity.py
----------------------------------------------------------------------------
Reference:
[1] Sidhu, J. (2022). Inter-lobar Connectivity of the Frontal Lobe Association
    Tracts Consistently Observed in 105 Healthy Adults
    (Doctoral dissertation, Université de Sherbrooke).
----------------------------------------------------------------------------
"""

import argparse
import logging

import numpy as np

from scilpy.image.volume_math import invert
from scilpy.io.utils import (add_overwrite_arg, add_verbose_arg,
                             assert_outputs_exist,
                             load_matrix_in_any_format,
                             save_matrix_in_any_format, assert_inputs_exist)
from scilpy.version import version_string

def _build_arg_parser():
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawTextHelpFormatter,
                                epilog=version_string)

    p.add_argument('out_matrix_mask',
                   help='Output mask (matrix) resulting from the provided '
                        'conditions (.npy).')

    p.add_argument('--lower_than', nargs='*', action='append', default=[],
                   metavar='MATRICES_LIST VALUE_THR POPULATION_PERC',
                   help='Lower than condition using the VALUE_THR in '
                        'at least POPULATION_PERC (from MATRICES_LIST).\n'
                        'See description for more details.')
    p.add_argument('--greater_than', nargs='*', action='append', default=[],
                   metavar='MATRICES_LIST VALUE_THR POPULATION_PERC',
                   help='Greater than condition using the VALUE_THR in '
                        'at least POPULATION_PERC (from MATRICES_LIST).\n'
                        'See description for more details.')

    p.add_argument('--keep_condition_count', action='store_true',
                   help='Report the number of condition(s) that pass/fail '
                        'rather than a binary mask.')
    p.add_argument('--inverse_mask', action='store_true',
                   help='Inverse the final mask. 0 where all conditions are '
                        'respected and 1 where at least one fail.')

    add_verbose_arg(p)
    add_overwrite_arg(p)

    return p


def _filter(input_list, condition):
    matrices = [load_matrix_in_any_format(i) for i in input_list[:-2]]
    shape = matrices[0].shape
    matrices = np.rollaxis(np.array(matrices), axis=0, start=3)
    value_threshold = float(input_list[-2])
    population_threshold = int(float(input_list[-1]) * matrices.shape[-1])

    empty_matrices = np.zeros(matrices.shape)
    # Only difference between both condition, the rest is identical
    if condition == 'lower':
        empty_matrices[matrices < value_threshold] = 1
    else:
        empty_matrices[matrices > value_threshold] = 1
    population_score = np.sum(empty_matrices, axis=2)

    filter_mask = population_score > population_threshold
    logging.info('Condition {}_than resulted in {} filtered '
                 'elements out of {}.'
                 .format(condition, np.count_nonzero(~filter_mask),
                         np.prod(shape)))

    return filter_mask


def main():
    parser = _build_arg_parser()
    args = parser.parse_args()
    logging.getLogger().setLevel(logging.getLevelName(args.verbose))

    inputs = [m for cond in args.lower_than for m in cond[:-2]]
    inputs.extend([m for cond in args.greater_than for m in cond[:-2]])
    assert_inputs_exist(parser, inputs)
    assert_outputs_exist(parser, args, args.out_matrix_mask)

    if not args.lower_than and not args.greater_than:
        parser.error('At least one of the two options is required.')

    conditions_list = []
    if args.lower_than:
        for input_list in args.lower_than:
            conditions_list.append(('lower', input_list))
    if args.greater_than:
        for input_list in args.greater_than:
            conditions_list.append(('greater', input_list))

    condition_counter = 0
    shape = load_matrix_in_any_format(conditions_list[0][1][0]).shape
    output_mask = np.zeros(shape)

    for input_list in args.lower_than:
        condition_counter += 1
        filter_mask = _filter(input_list, 'lower')
        output_mask[filter_mask] += 1

    for input_list in args.lower_than:
        condition_counter += 1
        filter_mask = _filter(input_list, 'gteater')
        output_mask[filter_mask] += 1

    if not args.keep_condition_count:
        output_mask[output_mask < condition_counter] = 0
        output_mask[output_mask > 0] = 1

    if args.inverse_mask:
        if args.keep_condition_count:
            output_mask = np.abs(output_mask - np.max(output_mask))
        else:
            output_mask = invert([output_mask], ref_img=None)

    filtered_elem = np.prod(shape) - np.count_nonzero(output_mask)

    # To prevent mis-usage, --keep_condition_count should not be used for
    # masking without binarization first
    if args.keep_condition_count:
        logging.warning('Keeping the condition count is not recommanded for '
                        'filtering.\nApply threshold manually to binarize the '
                        'output matrix.')
    else:
        logging.info('All condition resulted in {} filtered '
                     'elements out of {}.'.format(filtered_elem,
                                                  np.prod(shape)))

    save_matrix_in_any_format(args.out_matrix_mask,
                              output_mask.astype(np.uint8))


if __name__ == '__main__':
    main()
