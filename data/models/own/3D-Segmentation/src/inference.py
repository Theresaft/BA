"""This module is responsible for running the PyTorch model we trained. This model is located in models/ and it's a
PyTorchLightning checkpoint. The version of the Segmenter object in segmenter.py, which is a Pytorch Lightning module,
should match with the Segmenter version used for the checkpoint, otherwise it may happen that hyperparameters are missing.
"""

import os
import torch
import torch.nn.functional as F
import torchio as tio
from argparse import Namespace, ArgumentParser
from segmenter import Segmenter

def get_cmd_args() -> Namespace:
    """Get the CMD arguments: --lightning-checkpoint, --input-path, and --output-path are required arguments, while --device is optional."""
    parser = ArgumentParser()

    parser.add_argument("--lightning-checkpoint", dest="lightning_checkpoint", required=True,
                        help="The location of the Pytorch Lightning checkpoint, which represents the actual model. Has to be compatible "
                        "with the current version of segmenter.py.")
    parser.add_argument("--input-path", dest="input_path", required=True,
                        help="The path to the input files, which are expected to be NIFTI files and should have the "
                        "format 'nifti_{seq}_register.nii.gz', where '{seq}' corresponds to flair, t1_norm, t1c, t2. The model "
                        "expects each of these sequences with exactly those names, otherwise the input is considered invalid.")
    parser.add_argument("--output-path", dest="output_path", required=True,
                        help="The path in which the segmentations should be stored. Per segmentation, we store one nii.gz")
    parser.add_argument("--patch-overlap", dest="patch_overlap", default=8,
                        help="By how many pixels the inferred patches should overlap.")
    parser.add_argument("--device", dest="device", default="cuda",
                        choices=["auto", "cpu", "gpu", "cuda", "mps", "tpu"],
                        help="Which device to use, e.g., 'cpu' or 'gpu'. "
                             "Full list: https://lightning.ai/docs/pytorch/stable/extensions/accelerator.html")
    args = parser.parse_args()

    return args


def main():
    """The main function fetches the CMD arguments, performs input validation, and runs the model. For that, we need a Pytorch Lightning
    checkpoint to extract the model. Similarly to how the training works, we split up the input image into 96x96x96 volumes with 4 channels
    because that is the input size that the model can accept. The patches are then reassembled into one large label map with the same
    size as the input image. This output label map is a NIFTI file that is placed in the --output-path."""
    # Get CMD arguments
    print("Running inference.py!")
    cmd_args: Namespace = get_cmd_args()

    # Input validation
    if not os.path.exists(cmd_args.lightning_checkpoint):
        print(f"The checkpoint '{cmd_args.lightning_checkpoint}' doesn't exist! Exiting with error...")
        exit(1)
    if not os.path.exists(cmd_args.input_path):
        print(f"The input path '{cmd_args.input_path}' doesn't exist! Exiting with error...")
        exit(1)
    if not cmd_args.patch_overlap.isdigit():
        print(f"The patch overlap {cmd_args.patch_overlap} should be a non-negative integer! Exiting with error...")
        exit(1)
    
    print("Parameters:", cmd_args)
    patch_overlap = int(cmd_args.patch_overlap)
    
    # Create a folder for the output path if necessary
    os.makedirs(cmd_args.output_path, exist_ok=True)

    # Load the model, set it to eval mode, and transfer it to the given device
    model = Segmenter.load_from_checkpoint(cmd_args.lightning_checkpoint)
    model.eval()
    model.to(cmd_args.device)

    hyperparams = model.hparams

    print("Model hyperparameters:")
    print(hyperparams)

    # Make a tio.Subject out of the images. The other tio utilities are for extracting patches
    # from the image and then reassembling them to create a valid image. Our model only takes
    # 96 by 96 by 96 input images, so we have to use this sampling strategy. There is an overlap
    # of 8 x 8 x 8 pixels. Since we get the images by sequence, we separately apply the process
    # function per sequence and then concatenate the rescaled tensors into one multi-channel tensor.
    
    paths = []
    num_sequences = 4
    # This is the order of sequences as written in dataset.json. We expect the sequences to be in the
    # following order: Flair, T1, T1c, T2
    for index in range(num_sequences):
        paths.append(os.path.join(cmd_args.input_path, f'_{index:04}.nii.gz'))
    
    # Some minor preprocessing
    process = tio.Compose([
        tio.RescaleIntensity((-1, 1))
    ])
    
    tensors = [tio.ScalarImage(path).data for path in paths]
    # We will use the image template later for its metadata
    image_template = tio.ScalarImage(paths[0])
    full_tensor = torch.cat(tensors)
    raw_subject = tio.Subject({"MRI": tio.ScalarImage(tensor=full_tensor)})
    subject = tio.SubjectsDataset([raw_subject], transform=process)[0]
    print("Subject dimension:", subject["MRI"].shape)

    grid_sampler = tio.inference.GridSampler(subject, hyperparams["patch_size"], (patch_overlap, patch_overlap, patch_overlap))
    print("Overlap:", grid_sampler.patch_overlap)
    print("Patch size:", grid_sampler.patch_size)
    aggregator = tio.inference.GridAggregator(grid_sampler)
    patch_loader = torch.utils.data.DataLoader(grid_sampler, batch_size=4)

    # This is the actual prediction of the segmentation
    with torch.no_grad():
        for patches_batch in patch_loader:
            input_tensor = patches_batch["MRI"]["data"].to(cmd_args.device)
            locations = patches_batch[tio.LOCATION]
            pred = model(input_tensor)
            # We keep adding batches to the aggregator to later collect all the data.
            aggregator.add_batch(pred, locations)

    # The prediction is composed of the patches we have generated before
    pred = aggregator.get_output_tensor().argmax(0).unsqueeze(dim=0).to(torch.uint8)
    # Save the prediction in a nifti file as integer encoding, i.e., not one-hot-encoded.
    # As a template, take the Flair sequence (we could use any other, too, but need valid)
    # metadata.
    image_template.set_data(pred)
    image_template.save(os.path.join(cmd_args.output_path, ".nii.gz"))
    print("Prediction shape:", pred.shape)


if __name__ == "__main__":
    main()