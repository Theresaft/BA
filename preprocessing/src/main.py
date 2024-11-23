import sys
import os
import argparse

import SimpleITK as sitk

import brainpp_config as config
from preprocess.resample import resample_images
from preprocess.skullstrip import skullstrip_images
from preprocess.register import rigid_register
from dicom2nifti import dicom2nifti

description = ''' 
Neural Pre-processing (NPP) converts Head MRI images
to an intensity-normalized, skull-stripped brain in a standard coordi-
nate space. If you use NPP in your analysis, please cite:
'''


def main():
    # parse command line
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument('-p', '--subject_id', metavar='str', default='Pat_5_preop', help='Set the id or prefix for the subject.')
    parser.add_argument('-i', '--input_folder', metavar='folder_path', default=config.DATADIR, help='set alternative folder to input data.')
    parser.add_argument('-o', '--output_folder', metavar='folder_path', default=config.RESULTDIR, help='set alternative output folder.')
    parser.add_argument('-w', '--weight', metavar='float', help='Smoothness of intensity normalization mapping. The range of smoothness is [-3,2],'
                                                                ' where a larger value implies a higher degree of smoothing',default =-1)
    parser.add_argument('-s', '--field', action='store_true', help='Save the scalar field map.')
    parser.add_argument('-g', '--gpu', action='store_true', help='Use the GPU.')

    if len(sys.argv) < 1:
        parser.print_help()
        exit(1)

    args = parser.parse_args()

    assert os.path.isdir(args.input_folder), f"Base input folder is not a directory: {args.input_folder} "
    assert os.path.isdir(args.output_folder), f"Base output folder is not a directory: {args.output_folder} "
    subject_folder = os.path.join(args.input_folder, args.subject_id)
    assert os.path.isdir(subject_folder), f"Subject id {args.subject_id} is not present. Subject input folder is not a directory: {subject_folder}"
    assert os.path.isdir(config.FSLDIR), f"FSL directory {config.FSLDIR} does not exist!"

    dicom2nifti()

    subject = config.SubjectConfig(args.subject_id, args.input_folder, args.output_folder)
    subject.init_filenames()
    subject.init_meta()
    for sequ in [k for k in subject.input_files if subject.input_files[k] is not None]:
        print(f'Subject {args.subject_id} found sequence {sequ} in {subject.input_files[sequ]}')
    assert not any([True for seq in subject.input_files.keys()
                    if seq in config.RequiredSequences and subject.input_files[seq] is None]), \
        f"Required sequences are missing! Required are {config.RequiredSequences} {subject.input_files}"

    print(subject)
    print(subject.input_meta)

    skullstrip_images(subject, weight=args.weight)
    resample_images(subject, re_center=True)
    rigid_register(subject, reference_seq='t1c')

    final_sequences = list(config.SequenceNames) + ['brainmask', 'resample_mask', 't1_norm']
    brainmask = sitk.ReadImage(subject.register_files['brainmask'])
    for seq in final_sequences:
        if seq not in subject.register_files or subject.register_files[seq] is None or not os.path.exists(subject.register_files[seq]):
            print(f"WARNING registered sequence {seq} for subject {subject.subject_id} is missing!")
            continue
        outfile = os.path.join(subject.get_output_dir(), f"{subject.subject_id}_{seq}_register.nii.gz")
        if seq in config.SequenceNames:
            print("  Mask sequence {} with brain mask ...".format(seq))
            image = sitk.ReadImage(subject.register_files[seq])
            image = sitk.Mask(image=image, maskImage=brainmask, outsideValue=0)
            sitk.WriteImage(image, outfile)
        else:
            print("  Copy sequence {} ...".format(seq))
            syscall = "cp {} {}".format(subject.register_files[seq], outfile)
            print("    >> {}".format(syscall))
            os.system(syscall)


# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    main()

