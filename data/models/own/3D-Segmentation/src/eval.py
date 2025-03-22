import torch
import pytorch_lightning as pl
from pytorch_lightning.callbacks import ModelCheckpoint
from pytorch_lightning.loggers import TensorBoardLogger
import torchio as tio
from pathlib import Path
import matplotlib.pyplot as plt
import numpy as np
from tqdm.notebook import tqdm
import torch.nn.functional as F
import os
import shutil
import csv
from dice_loss import DiceLoss
from argparse import ArgumentParser, Namespace

from segmenter import Segmenter


# ------------- Helper functions

def get_cmd_args() -> Namespace:
    parser = ArgumentParser()
    parser.add_argument("--data-root-path", dest="data_root_path",
                        help="The directory where the training and label data are located."
                             "It is assumed that the training data can be found under 'imagesTr/' and the label "
                             "data can be found under 'labelsTr/' as NIFTI files.")
    parser.add_argument("--checkpoint-root-path", dest="checkpoint_root_path",
                        help="The root directory of the checkpoints, which will typically end with "
                             "'logs/lightning_logs/'. Relatively to that, you can specify the version folder using "
                             "--version-folder.")
    parser.add_argument("--version-folder", dest="version_folder",
                        help="Relatively to the root path, where the version folder, e.g., version_17 is located. "
                             "It is assumed that inside that folder, a checkpoints folder is located containing "
                             "the checkpoints.")
    parser.add_argument("--output-root-path", dest="output_root_path",
                        help="The root output directory for the images, the best model checkpoint, and some metadata "
                             "on the best checkpoint.")
    parser.add_argument("--patch-overlap", dest="patch_overlap", default=8,
                        help="By how many pixels the inferred patches should overlap.")
    parser.add_argument("--device", dest="device", default="cuda",
                        choices=["auto", "cpu", "gpu", "cuda", "mps", "tpu"],
                        help="Which device to use, e.g., 'cpu' or 'gpu'. "
                             "Full list: https://lightning.ai/docs/pytorch/stable/extensions/accelerator.html")
    parser.add_argument("--train-split-percent", dest="train_split_percent", default="85",
                        help="The number of elements to train with per batch (with or without quotation marks).")
    parser.add_argument("--slices-to-show", dest="slices_to_show", default="30,40,50,60,70,80,90,100,110",
                        help="The slices per shown subject to create an image for. The numbers should be "
                             "comma-separated, without spaces and in the range of [0, no. slices per scan - 1].")
    args = parser.parse_args()

    return args


def get_models_and_metadata(version_path: str):
    path = Path(version_path + "/checkpoints")

    checkpoint_paths = list(path.glob("*"))
    model_list = []
    metadata_list = []
    # Keep track of whether the error output concerning the missing hyperparameter has been output already. We
    # only want to output the error message once, not for every checkpoint. So after the first output, this
    # variable is set to True.
    error_output = False

    for path in checkpoint_paths:
        metadata = torch.load(path)
        metadata_list.append(metadata)

        model = Segmenter.load_from_checkpoint(path)

        # Append the current model to the list of models, out of which we will later select the best one.
        model_list.append(model)

    # Since the models and the metadata is stored separately, we also return them as separate lists.
    return model_list, metadata_list


def change_img_to_label_path(path):
    """ Returns all directories in a path. """
    parts = list(path.parts)
    # Replace path
    parts[parts.index("imagesTr")] = "labelsTr"
    return Path(*parts)


def masked(a):
    return np.ma.masked_where(a == 0, a)


def show_mri_and_pred(ground_truth, subject_num, slice_num, pred, train=False, save=False):
    plt.figure()
    plt.imshow(ground_truth[subject_num]["MRI"].data[0,:,:,slice_num], cmap="bone")
    max_likelihood_pred = pred.argmax(0)
    plt.imshow(masked(max_likelihood_pred[:, :, slice_num]), alpha=0.5, cmap="autumn")
    title_start = "Training" if train else "Eval"
    plt.title(f"{title_start} subject {subject_num}, slice {slice_num}")
    plt.suptitle("Prediction", y=0.05, fontsize=10)
    if save:
        plt.savefig(f"{subject_num}-{slice_num}.png")


def show_all(ground_truth, subject_num, slice_num, pred, save=False, save_root_path="imgs/",
             save_file_name="", extra_pred_text=""):
    if save:
        plt.ioff()
    f, ax = plt.subplots(2)
    # Show ground truth image
    ax[0].set_position([0, 0, 0.8, 0.8])
    ax[0].imshow(ground_truth[subject_num]["MRI"].data[0, :, :, slice_num], cmap="bone")
    ax[0].imshow(masked(ground_truth[subject_num]["Label"].data[0, :, :, slice_num]), alpha=0.5,
                 cmap="autumn")
    title_start = "Training"
    ax[0].set_title(f"{title_start} subject {subject_num}, slice {slice_num} \n(ground truth)")
    # ax[0].legend("Ground truth", y=0.05, fontsize=10)

    # Show prediction image
    ax[1].set_position([0.75, 0, 0.8, 0.8])
    ax[1].imshow(ground_truth[subject_num]["MRI"].data[0, :, :, slice_num], cmap="bone")
    max_likelihood_pred = pred.argmax(0)
    ax[1].imshow(masked(max_likelihood_pred[:, :, slice_num]), alpha=0.5, cmap="autumn")
    title_start = "Training"
    extra_text = "" if extra_pred_text == "" else ", " + extra_pred_text
    ax[1].set_title(f"{title_start} subject {subject_num}, slice {slice_num} \n(pred{extra_text})")
    if save:
        plt.savefig(f"{save_root_path}/{save_file_name}.png", dpi=200, bbox_inches="tight")
        plt.ion()
    plt.close()


def save_plots_for_index(ground_truth, pred, subject_num, slices, save_root_path, save_file_name, extra_pred_text=""):
    for slice_num in slices:
        show_all(ground_truth, subject_num, slice_num, pred.squeeze(), save=True, save_root_path=save_root_path,
                 save_file_name=save_file_name + f"-slice={slice_num}", extra_pred_text=extra_pred_text)


def write_loss_list_data(csv_file, loss_list):
    with open(csv_file, "w", newline="") as file:
        writer = csv.writer(file, delimiter=";")
        # Title row
        writer.writerow(["Rank of subject", "Subject loss", "Subject number"])
        for index, loss_data in enumerate(loss_list):
            loss, subject_num = loss_data
            writer.writerow([index + 1, loss.item(), subject_num])


def write_loss_metrics(csv_file, loss_list):
    with open(csv_file, "w", newline="") as file:
        writer = csv.writer(file, delimiter=";")
        cleaned_loss = torch.tensor([loss.item() for (loss, subject_num) in loss_list])
        # Title row
        writer.writerow(["Loss metric", "Value"])
        # Metric rows
        writer.writerow(["Mean", cleaned_loss.mean().item()])
        writer.writerow(["Minimum", cleaned_loss.min().item()])
        writer.writerow(["Median", cleaned_loss.median().item()])
        writer.writerow(["Maximum", cleaned_loss.max().item()])
        writer.writerow(["Standard deviation", cleaned_loss.std().item()])


def write_hyperparameters(csv_file: str, hyperparameters: dict):
    with open(csv_file, "w", newline="") as file:
        writer = csv.writer(file, delimiter=";")
        # Title row
        writer.writerow(["Hyperparameter", "Value"])
        # Hyperparameter rows
        for param_name, param_value in hyperparameters.items():
            writer.writerow([param_name, param_value])


def main():
    # ----------- Reading CMD arguments
    # Fetch CMD arguments
    cmd_args: Namespace = get_cmd_args()

    if not cmd_args.patch_overlap.isdigit():
        print(f"The patch overlap {cmd_args.patch_overlap} should be a non-negative integer! Exiting with error...")
        exit(1)

    version_folder = cmd_args.version_folder + "/"
    device = cmd_args.device
    checkpoint_root_path = cmd_args.checkpoint_root_path + "/"
    data_root_path = cmd_args.data_root_path
    output_root_path = cmd_args.output_root_path + "/" + version_folder
    slices_to_show = [int(x) for x in cmd_args.slices_to_show.split(",")]
    train_split = float(cmd_args.train_split_percent) / 100
    patch_overlap = int(cmd_args.patch_overlap)

    print(f"Using device {device}")
    print(f"Slices to show: {slices_to_show}")

    # Create the directories and subdirectories required for the evaluation
    if not os.path.isdir(output_root_path + "/images/"):
        os.makedirs(output_root_path + "/images/")
    if not os.path.isdir(output_root_path + "/model/"):
        os.makedirs(output_root_path + "/model/")
    if not os.path.isdir(output_root_path + "/metadata/"):
        os.makedirs(output_root_path + "/metadata/")

    # Load the best k models and the corresponding metadata
    models, metadatas = get_models_and_metadata(checkpoint_root_path + version_folder)

    # Load the validation subjects
    path = Path(data_root_path + "/imagesTr")
    subject_paths = list(path.glob("BRATS_*"))
    subjects = []

    for subject_path in subject_paths:
        label_path = change_img_to_label_path(subject_path)
        subject = tio.Subject({"MRI": tio.ScalarImage(subject_path),
                               "Label": tio.LabelMap(label_path)})
        subjects.append(subject)

    # Preprocess the validation data
    process = tio.Compose([
        tio.RescaleIntensity((-1, 1))
    ])

    split_index = int(len(subjects) * train_split)
    val_dataset = tio.SubjectsDataset(subjects[split_index:], transform=process)

    # Iterate all saved checkpoints, i.e., the model with the metadata and find out which one performs best on the
    # validation data. That best model will be used to perform more in-depth analysis on the loss and to visualize
    # the segmented tumors of the model.
    loss_per_model = []
    all_losses = []

    for index, (model, metadata) in enumerate(zip(models, metadatas)):
        # Switch the model to eval mode
        model.eval()
        model.to(device)
        total_loss = 0.0
        epoch = metadatas[index]['epoch']
        preds = []
        losses = []

        print(f"----- Evaluating model no. {index} for epoch {epoch} -----")

        # Load the patches from the current subject
        for subject_num in range(len(val_dataset)):
            if subject_num % 10 == 0:
                print("\t\tSubject no.", subject_num)

            patch_size = metadatas[index]["hyper_parameters"]["patch_size"]
            grid_sampler = tio.inference.GridSampler(val_dataset[subject_num], patch_size, (patch_overlap, patch_overlap, patch_overlap))
            aggregator = tio.inference.GridAggregator(grid_sampler)
            patch_loader = torch.utils.data.DataLoader(grid_sampler, batch_size=4)

            with torch.no_grad():
                for patches_batch in patch_loader:
                    input_tensor = patches_batch["MRI"]["data"].to(device)
                    locations = patches_batch[tio.LOCATION]
                    pred = model(input_tensor)
                    # We keep adding batches to the aggregator to later collect all the data.
                    aggregator.add_batch(pred, locations)

            # pred = torch.swapaxes(F.one_hot(aggregator.get_output_tensor().argmax(0)).unsqueeze(dim=0), 0, 4).squeeze()
            # label = torch.swapaxes(F.one_hot(val_dataset[0]["Label"].data.long()), 0, 4).squeeze()

            pred = aggregator.get_output_tensor().unsqueeze(dim=0)
            label = val_dataset[subject_num]["Label"].data.long()

            # Elementwise equality check
            loss = DiceLoss()(pred, label)
            preds.append(pred)
            losses.append(loss)
            total_loss += loss

        average_loss = total_loss / len(val_dataset)
        loss_per_model.append((average_loss, epoch))
        print(f"Average loss: {average_loss}")

        # Visualization for the 0th, 25th, 50th, 75th, and 100th percentile of the losses.
        mod_losses = [(loss, index) for index, loss in enumerate(losses)]
        sorted_losses = sorted(mod_losses)
        print("All losses:", sorted_losses)
        all_losses.append(sorted_losses)

        # The loss of the worst prediction (0th percentile).
        worst_loss, worst_index = sorted_losses[-1]
        # The loss of the 25th percentile prediction.
        perc_25_loss, perc_25_index = sorted_losses[int(len(sorted_losses) * 0.75)]
        # The median loss of the predictions (50th percentile).
        median_loss, median_index = sorted_losses[int(len(sorted_losses) * 0.5)]
        # The loss of the 75th percentile prediction.
        perc_75_loss, perc_75_index = sorted_losses[int(len(sorted_losses) * 0.25)]
        # The loss of the best prediction (100th percentile).
        best_loss, best_index = sorted_losses[0]

        # Visualize all the losses for the specified slice indices.
        save_plots_for_index(val_dataset, preds[worst_index], worst_index, slices_to_show, output_root_path + "/images/",
                             f"epoch={epoch}-perc=0",
                             f"0th percentile, loss={worst_loss * 100:.2f}%")

        save_plots_for_index(val_dataset, preds[perc_25_index], perc_25_index, slices_to_show, output_root_path + "/images/",
                             f"epoch={epoch}-perc=25",
                             f"25th percentile, loss={perc_25_loss * 100:.2f}%")

        save_plots_for_index(val_dataset, preds[median_index], median_index, slices_to_show, output_root_path + "/images/",
                             f"epoch={epoch}-perc=50",
                             f"50th percentile, loss={median_loss * 100:.2f}%")

        save_plots_for_index(val_dataset, preds[perc_75_index], perc_75_index, slices_to_show, output_root_path + "/images/",
                             f"epoch={epoch}-perc=75",
                             f"75th percentile, loss={perc_75_loss * 100:.2f}%")

        save_plots_for_index(val_dataset, preds[best_index], best_index, slices_to_show, output_root_path + "/images/",
                             f"epoch={epoch}-perc=100",
                             f"100th percentile, loss={best_loss * 100:.2f}%")

    print("\n\nDONE with evaluating data!")
    print("\n\n\nLoss per model:", sorted(loss_per_model))

    # Get the best data
    best_avg_loss, best_epoch = sorted(loss_per_model)[0]
    best_index = [metadata["epoch"] for metadata in metadatas].index(best_epoch)
    hyperparameters = metadatas[best_index]["hyper_parameters"]
    print(best_avg_loss, "epoch:", best_epoch, "index:", best_index)

    # Delete all images from the epochs that are not the best epoch.
    for file in os.listdir(output_root_path + "/images/"):
        if not file.startswith(f"epoch={best_epoch}"):
            os.remove(output_root_path + "/images/" + file)
    print(f"Removed images for non-optimal models!")

    # Copy the best checkpoint to the checkpoint subdirectory
    path = Path(checkpoint_root_path + version_folder + "/checkpoints")
    checkpoint_path = next(path.glob(f"epoch={best_epoch}*"))
    new_checkpoint_path = output_root_path + "/model/"
    shutil.copy(checkpoint_path, new_checkpoint_path)
    print(f"Copied checkpoint to {new_checkpoint_path}!")

    # Save the metadata
    metadata_path = output_root_path + "/metadata/"
    loss_list_for_best = all_losses[best_index]
    write_loss_list_data(metadata_path + "loss_list.csv", loss_list_for_best)
    write_loss_metrics(metadata_path + "loss_metrics.csv", loss_list_for_best)
    write_hyperparameters(metadata_path + "hyperparameters.csv", hyperparameters)

    print("Done writing data to files!")


if __name__ == "__main__":
    main()
