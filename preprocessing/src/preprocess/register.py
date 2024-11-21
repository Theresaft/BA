import os
import datetime
import subprocess

from numpy.distutils.command.config import config

import brainpp_config as config


def rigid_register(subject: config.SubjectConfig, reference_seq='t1', force=False):
    assert os.path.isdir(config.FSLDIR), f"FSL not found in {config.FSLDIR} !"
    os.environ["FSLOUTPUTTYPE"] = "NIFTI_GZ"
    FLIRTCMD = os.path.join(config.FSLDIR, 'bin', 'flirt')
    assert os.path.isfile(FLIRTCMD), f"FSL flirt not found in {FLIRTCMD} !"
    # Initialize output directory and logging info
    patid = subject.subject_id
    OUTPATDIR = subject.get_working_dir()
    os.makedirs(OUTPATDIR, exist_ok=True)

    logger = config.setup_logger('register', os.path.join(OUTPATDIR, "rigid_register.log"))
    logger.info("Start Registration at " + datetime.datetime.now().strftime("%d. %m. %Y at %H:%M:%S"))
    logger.info("Patient: " + patid)

    # check if reference sequence is already resampled
    reference_image_filename = subject.resample_files[reference_seq] if reference_seq in subject.resample_files else None
    if reference_image_filename is None or not os.path.isfile(reference_image_filename):
        logger.error('ERROR: No resampled reference file for patient {} !'.format(patid))
        logger.error('ERROR: Expected reference file: {}'.format(reference_image_filename))
        return False

    registration_dict = dict()
    for sequ in subject.resample_files:
        registration_dict[sequ] = {
            'input': subject.resample_files[sequ],
            'output': os.path.join(OUTPATDIR, f"{patid}_{sequ}_register.nii.gz"),
            'transform': os.path.join(OUTPATDIR, f"{patid}_{sequ}_registered.lta"),
            'co_registered_to': subject.same_coordinates[sequ] if sequ in subject.same_coordinates else [],
            'interpolation': 'trilinear' if sequ not in subject.label_sequences else 'nearestneighbour -datatype char'
        }
    logger.debug(f"Registration info: {registration_dict}")

    #
    # Start registration of all sequences
    #
    ready_registered = []
    reffile = reference_image_filename
    for sequ in subject.resample_files:
        sequ_dict = registration_dict[sequ]
        infile = sequ_dict['input']
        outfile = sequ_dict['output']
        co_registered_sequ = [s for s in ready_registered if s in sequ_dict['co_registered_to']]
        co_registered_lta = None if not co_registered_sequ else registration_dict[co_registered_sequ[0]]['transform']
        # check if sequence exists
        if infile is None or not os.path.isfile(infile):
            logger.warning('WARNING: No resampled {} sequence file for patient {} found !'.format(sequ, patid))
            continue

        if sequ == reference_seq:
            logger.info("  Copy sequence {} ...".format(sequ))
            syscall = "cp {} {}".format(sequ_dict['input'], sequ_dict['output'])
            logger.info("    >> {}".format(syscall))
            os.system(syscall)
        elif sequ_dict['co_registered_to'] is not None and reference_seq in sequ_dict['co_registered_to']:
            logger.info("  Copy sequence {} (co-registered with {}) ...".format(sequ, reference_seq))
            syscall = "cp {} {}".format(sequ_dict['input'], sequ_dict['output'])
            logger.info("    >> {}".format(syscall))
            os.system(syscall)
        elif co_registered_lta is not None:
            logger.info("  Transform sequence {} (apply transform of co-registered sequence {}) ...".format(sequ, co_registered_sequ[0]))
            # check for lta file
            if not os.path.isfile(co_registered_lta):
                logger.error("ERROR: transform file of sequence {} does not exist - re-order processing list of sequences !".format(sequ_dict['co_registered_to']))
                continue
            interp = sequ_dict['interpolation']
            syscall = "{} -in {} -ref {} -applyxfm -init {} -interp {} -out {}".format(FLIRTCMD, infile, reffile, co_registered_lta, interp, outfile)
            logger.info("    >> {}".format(syscall))
            call_output = subprocess.run(syscall.split(), stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
            logger.info("    {}".format(call_output.stdout.decode('utf-8')))
        else:
            logger.info("  Register {} to {} ...".format(sequ, reference_seq))
            out_lta_file = sequ_dict['transform']
            interp = sequ_dict['interpolation']
            if not os.path.exists(out_lta_file) or force:
                #CALL="${FSLPATH}/bin/flirt -in ${t1_image} -ref ${t1c_image} -omat ${out_t1_transform} -o ${out_t1_image} -cost normmi -dof 9"
                syscall = "{} -in {} -ref {} -omat {} -interp {} -o {} -cost normmi -dof 9 -v".format(FLIRTCMD, infile, reffile, out_lta_file, interp, outfile)
                logger.info("    >> {}".format(syscall))
                call_output = subprocess.run(syscall.split(), stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
                logger.debug("    {}".format(call_output.stdout.decode('utf-8')))
            else:
                logger.info("  Transform file exist, SKIP registration.")
        ready_registered.append(sequ)
        subject.register_files[sequ] = sequ_dict['output']

    for sequ in subject.register_files:
        logger.info(f"  Sequence {sequ} registered in {subject.register_files[sequ]}")

    logger.info("Finished Co-Registration at " + datetime.datetime.now().strftime("%d. %m. %Y at %H:%M:%S"))
    logger.info("Finished.")
    for h in logger.handlers:
        h.flush()

