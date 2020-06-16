#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import tempfile

from scilpy.io.fetcher import fetch_data, get_home, get_testing_files_dict 

# If they already exist, this only takes 5 seconds (check md5sum)
fetch_data(get_testing_files_dict(), keys=['atlas.zip'])
tmp_dir = tempfile.TemporaryDirectory()


def test_help_option(script_runner):
    ret = script_runner.run('scil_remove_labels.py', '--help')
    assert ret.success


def test_execution_atlas(script_runner):
    os.chdir(os.path.expanduser(tmp_dir.name))
    input_atlas = os.path.join(get_home(), 'atlas',
                               'atlas_freesurfer_v2.nii.gz')
    ret = script_runner.run('scil_remove_labels.py', input_atlas,
                            'atlas_freesurfer_v2_no_brainstem.nii.gz',
                            '-i', '173', '174', '175')
    assert ret.success
