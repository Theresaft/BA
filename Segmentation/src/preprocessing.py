from pathlib import Path
import nibabel as nib
import numpy as np
from argparse import ArgumentParser, Namespace

import torch
import torch.nn.functional as F
import os


def change_img_to_label_path(path, images_path_relative, labels_path_relative):
    """
    Replaces images path with labels path.
    """
    parts = list(path.parts)  # get all directories within the path
    parts[parts.index(images_path_relative)] = labels_path_relative  # Replace imagesTr with labelsTr
    return Path(*parts)  # Combine list back into a Path object


# Helper functions for normalization and standardization
def normalize(full_volume):
    mu = full_volume.mean()
    std = np.std(full_volume)
    normalized = (full_volume - mu) / std
    return normalized

def standardize(normalized):
    standardized = (normalized - normalized.min()) / (normalized.max() - normalized.min())
    return standardized

# Example: python preprocessing.py --root-dir "../Task01_BrainTumour" --output-dir "../Preprocessed"
def get_cmd_args() -> Namespace:
    parser = ArgumentParser()
    parser.add_argument("-r", "--root-dir", dest="root_dir",
                        help="The root directory where the segmentation data is located.")
    parser.add_argument("-i", "--training-images", dest="training_images", default="imagesTr",
                        help="Relatively to root-dir, the location of the training images directory")
    parser.add_argument("-l", "--training-labels", dest="training_labels", default="labelsTr",
                        help="Relatively to root-dir, the location of the training label directory")
    parser.add_argument("-o", "--output-dir", dest="output_dir",
                        help="Relatively to script directory, the location of the output")
    parser.add_argument("--training-percentage", dest="training_percentage", default="80",
                        help="The percentage of the total data that should be dedicated to training. The "
                             "rest goes to validation.")
    args = parser.parse_args()

    if args.root_dir is None:
        print("--root-dir argument can't be empty!")
        exit(-1)
    if args.output_dir is None:
        print("--output-dir argument can't be empty!")
        exit(-1)

    return args


def main():
    # Fetch root directory from cmd arguments
    cmd_args: Namespace = get_cmd_args()
    root = Path(cmd_args.root_dir)
    images_path_relative = cmd_args.training_images
    labels_path_relative = cmd_args.training_labels
    images_path = root/images_path_relative
    training_percentage = int(cmd_args.training_percentage) / 100

    images_list = list(images_path.glob("BRA*"))  # Get all subjects

    save_root = Path(cmd_args.output_dir)
    # This is the first image index that refers to the eval part. Every index smaller than that belongs to
    # training.
    train_eval_threshold = round(len(images_list) * training_percentage)

    # Iterate every 3D image. Each image has several 2D slices, hence the inner for loop.
    for counter, path_to_mri_data in enumerate(images_list):

        labels_path = change_img_to_label_path(path_to_mri_data, images_path_relative, labels_path_relative)

        mri = nib.load(path_to_mri_data)
        assert nib.aff2axcodes(mri.affine) == ("R", "A", "S")
        mri_data: np.ndarray = mri.get_fdata()

        # Load the label data as longs (int64) for the one-hot encoding below.
        label_data = nib.load(labels_path).get_fdata().astype(np.int64)
        num_unique_labels = len(np.unique(label_data))
        # Temporarily convert to a tensor for the one-hot encoding. Note that this converts it into a torch Tensor.
        one_hot_labels: torch.Tensor = F.one_hot(torch.from_numpy(label_data), num_unique_labels)

        # Normalize and standardize the images
        normalized_mri_data = normalize(mri_data)
        standardized_mri_data = standardize(normalized_mri_data)

        # Check if train or val data and create corresponding path
        if counter < train_eval_threshold:
            current_path = save_root/"train"/str(counter)
        else:
            current_path = save_root/"val"/str(counter)

        # Status message
        print(f"Preprocessing iteration {counter + 1} / {len(images_list)}")

        # Loop over the 2D slices in the full volume and store the images and labels in the data/masks directory.
        # We iterate over third dimension of standardized_mri_data because that's where the different slices
        # are located.
        for index in range(len(standardized_mri_data[0][0])):
            # Grab the current slice index and all the data in it
            slice = standardized_mri_data[:, :, index, :]
            # Convert the mask into a Numpy array because it's a Tensor.
            mask = one_hot_labels[:, :, index, :].numpy()

            # Move the channel dimension to the front, as expected by the model.
            slice = np.moveaxis(slice, [0, 1, 2], [1, 2, 0])
            mask = np.moveaxis(mask, [0, 1, 2], [1, 2, 0])

            slice_path = current_path/"data"
            mask_path = current_path/"masks"
            slice_path.mkdir(parents=True, exist_ok=True)
            mask_path.mkdir(parents=True, exist_ok=True)

            np.save(slice_path/str(index), slice)
            np.save(mask_path/str(index), mask)

if __name__ == "__main__":
    main()
        
    