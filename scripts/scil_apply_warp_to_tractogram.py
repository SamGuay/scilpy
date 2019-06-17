#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
    Warp *.trk using a non linear deformation.
    Can be used with Ants or Dipy deformation map.

    For more informations on how to use the various registration scripts
    see the doc/tractogram_registration.md readme file
"""

import argparse

import nibabel as nib
import numpy as np

from scilpy.io.utils import (add_overwrite_arg, create_header_from_anat,
                             assert_inputs_exist, assert_outputs_exists)
from scilpy.utils.filenames import split_name_with_nii
from scilpy.utils.streamlines import warp_tractogram


def transform_tractogram(in_filename, ref_filename, def_filename,
                         filename_to_save, field_source):
    in_tractogram = nib.streamlines.load(in_filename)

    _, out_extension = split_name_with_nii(filename_to_save)
    if out_extension == '.trk':
        # Only TRK/NII can be a reference, because they have an affine
        _, ref_extension = split_name_with_nii(ref_filename)
        if ref_extension == '.trk':
            ref_tractogram = nib.streamlines.load(ref_filename, lazy_load=True)
            ref_header = ref_tractogram.header
        else:
            ref_img = nib.load(ref_filename)
            ref_header = create_header_from_anat(ref_img)
    elif out_extension == '.tck':
        ref_header = nib.streamlines.TckFile.create_empty_header()

    deformation = nib.load(def_filename)
    deformation_data = np.squeeze(deformation.get_data())

    if not np.allclose(deformation.affine,
                       in_tractogram.header["voxel_to_rasmm"]):
        raise ValueError('Both affines are not equal')

    if not np.array_equal(deformation_data.shape[0:3],
                          in_tractogram.header["dimensions"]):
        raise ValueError('Both dimensions are not equal')

    transfo = in_tractogram.header["voxel_to_rasmm"]
    # Warning: Apply warp in-place
    warp_tractogram(in_tractogram.streamlines, transfo, deformation_data,
                    field_source)

    new_tractogram = nib.streamlines.Tractogram(in_tractogram.streamlines,
                                                affine_to_rasmm=np.eye(4))
    nib.streamlines.save(new_tractogram, filename_to_save, header=ref_header)


def _buildArgsParser():
    p = argparse.ArgumentParser(formatter_class=argparse.RawTextHelpFormatter,
                                description=__doc__)

    p.add_argument('in_file',
                   help='Path of the file that will be warped (*.trk).')

    p.add_argument('ref_file',
                   help='Path of the reference file, can be *.trk or '
                   'in the Nifti format')

    p.add_argument('deformation',
                   help='Path of the file containing the \n'
                   'deformation field.')

    p.add_argument('out_name',
                   help='Output filename of the transformed tractogram.')

    p.add_argument('--field_source', default='ants', choices=['ants', 'dipy'],
                   help='Source of the deformation field: \n'
                        '[ants, dipy] - be cautious, the default is ants')

    add_overwrite_arg(p)

    return p


def main():
    parser = _buildArgsParser()
    args = parser.parse_args()

    assert_inputs_exist(parser, [args.in_file, args.ref_file,
                                 args.deformation])
    assert_outputs_exists(parser, args, [args.out_name])

    if not nib.streamlines.TrkFile.is_correct_format(args.in_file):
        parser.error('The input file needs to be a TRK file')

    _, ref_extension = split_name_with_nii(args.ref_file)
    if ref_extension == '.trk':
        if not nib.streamlines.TrkFile.is_correct_format(args.ref_file):
            parser.error('{} is not a valid TRK file.'.format(args.ref_file))
    elif ref_extension not in ['.nii', '.nii.gz']:
        parser.error('{} is an unsupported format.'.format(args.ref_file))

    transform_tractogram(args.in_file, args.ref_file, args.deformation,
                         args.out_name, args.field_source)


if __name__ == "__main__":
    main()
