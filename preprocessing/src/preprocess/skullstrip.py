import SimpleITK as sitk
import sys
import time
import os
import datetime
import torch
import numpy as np
import nibabel as nib
import brainpp_config as config
from huggingface_hub import hf_hub_download
import surfa as sf
from nppy.models.model import UNet
from nppy.models.utils import normalize
from scipy.ndimage import binary_closing, binary_opening
import SimpleITK as sitk
import math
from importlib import reload

'''
def crop_or_pad_image(image: sitk.Image, size=(1,1,1)):
    dim = image.GetDimension()
    # look for padding
    lower_pad = 
    lower_pad, upper_pad = [0] * dim, [0] * dim
    for d in range(dim):
        lower_pad[d] =
        

def preprocess_image(image: sitk.Image):
    image = sitk.RescaleIntensity(sitk.Cast(image, sitk.sitkFloat32), outputMinimum=0, outputMaximum=1)
    image: sitk.Image = sitk.DICOMOrient(image, 'LIA')
    new_spacing = (1., 1.0, 1.0)
    output_size = tuple([int(math.ceil(s*si/sn)) for s, si, sn in zip(image.GetSize(), image.GetSpacing(), new_spacing)])
    image = sitk.Resample(image,
                          size = output_size,
                          outputOrigin=image.GetOrigin(),
                          outputSpacing=(1.0, 1.0, 1.0),
                          outputDirection=image.GetDirection())
'''


def skullstrip_images(subject: config.SubjectConfig, reference_seq='t1', weight=None, device='cpu'):
    assert subject.input_files[reference_seq] is not None, f"No input file for subject {subject.subject_id} and sequence {reference_seq}"

    checkpoint_path = hf_hub_download(repo_id="hexinzi/NeuralPreProcessing", filename="npp_v1.pth")
    #logging.shutdown()
    #reload(logging)

    # Initialize output directory and logging info
    patid = subject.subject_id
    OUTPATDIR = subject.get_working_dir()
    os.makedirs(OUTPATDIR, exist_ok=True)

    logger = config.setup_logger('skullstrip', os.path.join(OUTPATDIR, "skullstrip.log"))
    logger.info("Start Skullstripping at " + datetime.datetime.now().strftime("%d. %m. %Y at %H:%M:%S"))
    logger.info("Patient: " + patid)

    # check args.weight is in the range and float
    if weight is not None:
        weight = float(weight)
        assert -3.0 <= weight <= 2.0, 'The range of smoothness should within [-3,2], where a larger value implies a higher degree of smoothing'
    logger.info(f" weight: {weight}")

    # necessary for speed gains (I think)
    torch.backends.cudnn.benchmark = True
    torch.backends.cudnn.deterministic = True

    # configure GPU device
    is_gpu_available = torch.cuda.is_available()
    device = torch.device(device)
    # configure model
    logger.info(f'Configuring model on the {device}')

    with torch.no_grad():
        model = UNet()
        model.to(device)
        model.eval()

    version = '0.1'
    logger.info(f'Running Neural Pre-processing model version {version}')
    #cwd = os.getcwd()
    #modelfile = os.path.join(cwd,'models/checkpoints', f'npp_v{version}.pth')
    modelfile = checkpoint_path
    checkpoint = torch.load(modelfile, map_location=device)

    model.load_state_dict(checkpoint)

    # load image data for sequence for skullstrip
    input_path = subject.get_input_filename(reference_seq)
    image = sf.load_volume(input_path)
    logger.info(f'Input image read from: {input_path}')
    # frame check
    assert image.nframes <= 1, 'Input image cannot have more than 1 frame'

    #i normalize image to [0, 255] and to [0, 1]
    conformed = normalize(image.copy())
    # conform image and fit to shape with factors of 64
    conformed = conformed.conform(voxsize=1.0, dtype='float32',shape=(256,256,256), method='nearest', orientation='LIA')

    # predict the surface distance transform
    with torch.no_grad():
        input_tensor = torch.from_numpy(conformed.data[np.newaxis, np.newaxis]).to(device)
        output = model(input_tensor, weight)
        # mni_norm = output[0].cpu().numpy().squeeze().astype(np.int16)  # not used
        norm = output[1].cpu().numpy().squeeze().astype(np.int16)
        scalar_field = output[2].cpu().numpy().squeeze().astype(np.float32)

    logger.info(f'  generate brain mask and normalize {reference_seq} image.')
    # make brain_mask image and resampled as original image
    brain_mask = np.zeros_like(norm, dtype=np.uint8)
    brain_mask[norm > 0] = 1
    # morphological smoothing (note: scipy.ndimage.binary_opening() returns {0,1} images
    brain_mask = binary_opening(binary_closing(brain_mask, structure=np.ones((3,3,3))), structure=np.ones((3,3,3))).astype(np.uint8)
    brain_mask = conformed.new(brain_mask).resample_like(image, method='nearest',fill=0)
    # generate scalar field resampled as original image
    scalar_field = conformed.new(scalar_field).resample_like(image, method='linear',fill=0)
    # apply scalar field and brain mask to original image
    image.data = image.data * scalar_field.data * brain_mask.data

    logger.info(f'Save images to {OUTPATDIR} ... ')
    # write out brain mask, scalar_field and orig image normalized
    subject.skullstrip_files[f"{reference_seq}_norm"] = os.path.join(OUTPATDIR, f"{subject.subject_id}_{reference_seq}_norm.nii.gz")
    subject.same_coordinates[f"{reference_seq}_norm"] = [reference_seq]
    image.save(subject.skullstrip_files[f"{reference_seq}_norm"])
    subject.skullstrip_files[f"{reference_seq}_brainmask"] = os.path.join(OUTPATDIR, f"{subject.subject_id}_{reference_seq}_brainmask.nii.gz")
    subject.same_coordinates[f"{reference_seq}_brainmask"] = [reference_seq]
    subject.label_sequences.append(f"{reference_seq}_brainmask")
    # add key 'brainmask' in skullstrip dictionary
    subject.skullstrip_files["brainmask"] = subject.skullstrip_files[f"{reference_seq}_brainmask"]
    subject.same_coordinates["brainmask"] = [reference_seq]
    subject.label_sequences.append("brainmask")
    brain_mask.save(subject.skullstrip_files[f"{reference_seq}_brainmask"])
    subject.skullstrip_files[f"{reference_seq}_scalar_field"] = os.path.join(OUTPATDIR, f"{subject.subject_id}_{reference_seq}_scalar_field.nii.gz")
    subject.same_coordinates[f"{reference_seq}_scalar_field"] = [reference_seq]
    scalar_field.save(subject.skullstrip_files[f"{reference_seq}_scalar_field"])
    logger.debug(f'  saved skullstrip images: {subject.skullstrip_files}')

    logger.info("Finished skull stripping at " + datetime.datetime.now().strftime("%d. %m. %Y at %H:%M:%S"))
    logger.info("Finished.")


