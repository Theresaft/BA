import SimpleITK as sitk
import sys
import time
import os
import csv
import argparse
import logging
import datetime
import numpy as np
import brainpp_config as config


def calculate_threshold(image, relative_thresh=0.1):
    stat_filter = sitk.StatisticsImageFilter()
    stat_filter.Execute(image)
    imgmin = stat_filter.GetMinimum()
    imgmax = stat_filter.GetMaximum()
    thresh = imgmin + relative_thresh * (imgmax - imgmin)
    return thresh, imgmin, imgmax


def resample_images(subject: config.SubjectConfig, reference_seq=None, re_center=False):
    assert reference_seq is None or subject.input_files[reference_seq] is not None, f"No input file for subject {subject.subject_id} and sequence {reference_seq} "

    # Initialize output directory and logging info
    patid = subject.subject_id
    OUTPATDIR = subject.get_working_dir()
    os.makedirs(OUTPATDIR, exist_ok=True)

    logger = config.setup_logger('resample', os.path.join(OUTPATDIR, "resample.log"))
    logger.info("Start Resampling at " + datetime.datetime.now().strftime("%d. %m. %Y at %H:%M:%S"))
    logger.info("Patient: " + patid)

    if reference_seq is None:
        logger.info("Search for best reference sequence ...")
        # if not given, find best sequence as min(max(spacing))
        # read meta info if not already done
        subject.init_meta()
        # start with default reference sequence
        reference_seq = config.ReferenceSequence
        best_spacing = max(subject.input_meta[reference_seq]['spacing'])
        for seq in [k for k in subject.input_meta.keys() if subject.input_meta[k] is not None ]:
            spacing = subject.input_meta[seq]['spacing']
            print(spacing, max(spacing))
            if best_spacing > max(spacing):
                reference_seq = seq
                best_spacing = max(spacing)
        logger.info(f"  found sequence {reference_seq} with spacing {best_spacing}.")

    # Load reference image and log properties
    ref_file = subject.input_files[reference_seq]
    ref_image = sitk.ReadImage(ref_file)
    logger.info(f'Reference file: {ref_file}')
    logger.info('Reference file meta-data:')
    logger.info('  origin: ' + str(ref_image.GetOrigin()))
    logger.info('  size: ' + str(ref_image.GetSize()))
    logger.info('  spacing: ' + str(ref_image.GetSpacing()))
    logger.info('  direction: ' + str(ref_image.GetDirection()))
    logger.info('  pixel type: ' + str(ref_image.GetPixelIDTypeAsString()))
    logger.info('  number of pixel components: ' + str(ref_image.GetNumberOfComponentsPerPixel()))
    # output_file = output_dir + '/' + patid + '_' + 't1c' + '_resampled.nii.gz'
    # sitk.WriteImage(sitk.Cast(ref_image, sitk.sitkInt16), output_file)


    # Use meta data of reference image for resampling
    output_spacing = list(ref_image.GetSpacing())
    output_direction = ref_image.GetDirection()
    output_origin = ref_image.GetOrigin()
    output_size = list(ref_image.GetSize())

    # compute image center
    ref_extent = np.array(ref_image.GetSpacing()) * np.array(ref_image.GetSize())
    ref_center = np.array(ref_image.TransformContinuousIndexToPhysicalPoint(np.array(ref_image.GetSize()) / 2))
    logger.info('  extent: ' + str(ref_extent))
    logger.info('  center: ' + str(ref_center))

    # recompute size and spacing to get iso-voxels of 1x1x1mm³
    for dim in range(len(output_size)):
        output_size[dim] = int(output_size[dim] * output_spacing[dim])  # not sure if correct
        output_spacing[dim] = 1.0

    # set start transform to identity (we can think about using the image centers ... )
    transform = sitk.TranslationTransform(3, [0, 0, 0])
    transform.SetIdentity()

    # Select all sequences and files for resampling
    if (set(subject.input_files) - set(subject.skullstrip_files)) != set(subject.input_files):
        logger.error(f"There are duplicate keys in input_files and skullstrip!")
    # make sequence - file -- pairs for all images to resample
    sequ_file_pairs = list(subject.input_files.items()) + list(subject.skullstrip_files.items())

    mask_image = None
    seq_translation = None

    for sequence, seq_file in sequ_file_pairs:
        # seq_file = config.get_preprocess_filename(sequence, subject=subject, method='resample')
        if seq_file is None or not os.path.isfile(seq_file):
            logger.warning('WARNING: No {} sequence file for patient {} in {} !'.format(sequence, patid, seq_file))
            continue
        logger.info(f'Resample sequence {sequence} {"(segmentation)" if sequence in subject.label_sequences else ""}...')
        seq_image = sitk.ReadImage(seq_file)
        logger.info('  Before modification of sequence {}:'.format(sequence))
        logger.info('    origin: ' + str(seq_image.GetOrigin()))
        logger.info('    size: ' + str(seq_image.GetSize()))
        logger.info('    spacing: ' + str(seq_image.GetSpacing()))
        logger.info('    direction: ' + str(seq_image.GetDirection()))
        logger.info('    pixel type: ' + str(seq_image.GetPixelIDTypeAsString()))
        logger.info('    number of pixel components: ' + str(seq_image.GetNumberOfComponentsPerPixel()))
        # compute image center
        seq_extent = np.array(seq_image.GetSpacing()) * np.array(seq_image.GetSize())
        seq_center = np.array(seq_image.TransformContinuousIndexToPhysicalPoint(np.array(seq_image.GetSize()) / 2))
        logger.info('    extent: ' + str(seq_extent))
        logger.info('    center: ' + str(seq_center))
        # compute center distance and map centers
        if re_center:
            dist_to_ref_center = np.linalg.norm(seq_center - ref_center)
            if dist_to_ref_center > 0.1 * np.linalg.norm(seq_extent):
                logger.info('  Translate sequence ' + sequence + ' to match reference center!')
                if seq_translation is None:
                    seq_translation = seq_center - ref_center
                transform.SetOffset(seq_translation)
                logger.info('    translation: ' + str(transform.GetOffset()))
            else:
                transform.SetIdentity()

        logger.info(f'  Start resampling sequence {sequence} {"as segmentation" if sequence in subject.label_sequences else ""}...')
        resampled_image = sitk.Resample(seq_image, output_size, transform,
                                        sitk.sitkLinear if not sequence in subject.label_sequences else sitk.sitkLabelGaussian,
                                        output_origin, output_spacing, output_direction)

        logger.info('  After modification of sequence {}:'.format(sequence))
        logger.info('    origin: ' + str(resampled_image.GetOrigin()))
        logger.info('    size: ' + str(resampled_image.GetSize()))
        logger.info('    spacing: ' + str(resampled_image.GetSpacing()))
        logger.info('    direction: ' + str(resampled_image.GetDirection()))
        logger.info('    pixel type: ' + str(resampled_image.GetPixelIDTypeAsString()))
        logger.info('    number of pixel components: ' + str(resampled_image.GetNumberOfComponentsPerPixel()))

        output_file = os.path.join(OUTPATDIR, f"{subject.subject_id}_{sequence}_resample.nii.gz")
        subject.resample_files[sequence] = output_file
        # sitk.WriteImage(sitk.Cast(resampled_image, sitk.sitkInt16), output_file)
        logger.info(f"Save sequence {sequence} to {output_file} ... ")
        sitk.WriteImage(resampled_image, output_file)

        # update mask to show area of anatomical overlap, update mask only for base image sequences t1,t2, t1c flair
        if sequence in config.SequenceNames:
            logger.info('Update mask image ...')
            if mask_image is None:
                # initialize mask
                mask_image = sitk.BinaryThreshold(resampled_image, 25, 10000000)
            else:
                # update mask
                mask_image = sitk.Multiply(mask_image, sitk.BinaryThreshold(resampled_image, 25, 1000000))

    # print(mask_image)
    mask_file = os.path.join(OUTPATDIR, f'{subject.subject_id}_resample_mask.nii.gz')
    logger.info(f'Morphological smoothing and save mask image to {mask_file}.')
    mask_image = sitk.BinaryMorphologicalOpening(mask_image, (1,1,1))
    subject.resample_files['resample_mask'] = mask_file
    subject.same_coordinates['resample_mask'] = [reference_seq]
    subject.label_sequences.append('resample_mask')
    sitk.WriteImage(sitk.Cast(mask_image, sitk.sitkUInt8), mask_file)

    logger.info("Finished Resampling at " + datetime.datetime.now().strftime("%d. %m. %Y at %H:%M:%S"))
    logger.info("Finished.")

    print(f"######  {subject.skullstrip_files['brainmask']}")
