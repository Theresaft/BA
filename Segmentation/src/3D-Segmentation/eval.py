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

from segmenter import Segmenter

# TODO CMD arguments
version_folder = "version_17"
device = "cuda"
root = "C:/Users/denni/Documents/fallstudie-ss2024/logs/lightning_logs/"
data_root = "D:/Deep Learning/Task01_BrainTumour/"
output_root = "C:/Users/denni/Documents/fallstudie-ss2024/eval/" + version_folder
slices_to_show = [30, 40, 50, 60, 70, 80, 90, 100, 110]
train_split = 0.85


# ------------- Helper functions

def get_models_and_metadata(version_path: str):
    path = Path(version_path + "/checkpoints")

    checkpoint_paths = list(path.glob("*"))
    model_list = []
    metadata_list = []

    for path in checkpoint_paths:
        metadata = torch.load(path)
        metadata_list.append(metadata)

        # Dirty fix
        if "batch_size" not in metadata["hyper_parameters"]:
            model = Segmenter.load_from_checkpoint(path, batch_size=4)
        else:
            model = Segmenter.load_from_checkpoint(path)
        model_list.append(model)

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


def show_all(ground_truth, subject_num, slice_num, pred, train=False, save=False, save_root_path="imgs/",
             save_file_name="", extra_pred_text=""):
    # plt.figure(figsize=(20, 20))
    if save:
        plt.ioff()
    f, ax = plt.subplots(2)
    # Show ground truth image
    ax[0].set_position([0, 0, 0.8, 0.8])
    ax[0].imshow(ground_truth[subject_num]["MRI"].data[0, :, :, slice_num], cmap="bone")
    ax[0].imshow(masked(ground_truth[subject_num]["Label"].data[0, :, :, slice_num]), alpha=0.5,
                 cmap="autumn")
    title_start = "Training" if train else "Eval"
    ax[0].set_title(f"{title_start} subject {subject_num}, slice {slice_num} \n(ground truth)")
    # ax[0].legend("Ground truth", y=0.05, fontsize=10)

    # Show prediction image
    ax[1].set_position([0.75, 0, 0.8, 0.8])
    ax[1].imshow(ground_truth[subject_num]["MRI"].data[0, :, :, slice_num], cmap="bone")
    max_likelihood_pred = pred.argmax(0)
    ax[1].imshow(masked(max_likelihood_pred[:, :, slice_num]), alpha=0.5, cmap="autumn")
    title_start = "Training" if train else "Eval"
    extra_text = "" if extra_pred_text == "" else ", " + extra_pred_text
    ax[1].set_title(f"{title_start} subject {subject_num}, slice {slice_num} \n(pred{extra_text})")
    if save:
        plt.savefig(f"{save_root_path}/{save_file_name}.png", dpi=200, bbox_inches="tight")
        plt.ion()
    plt.close()


def save_plots_for_index(pred, subject_num, slices, save_root_path, save_file_name, extra_pred_text=""):
    for slice_num in slices:
        show_all(subject_num, slice_num, pred.squeeze(), save=True, save_root_path=save_root_path,
                 save_file_name=save_file_name + f"-slice={slice_num}", extra_pred_text=extra_pred_text)


def main():
    # Create the directories and subdirectories required for the evaluation
    if not os.path.isdir(output_root + "/images/"):
        os.makedirs(output_root + "/images/")
    if not os.path.isdir(output_root + "/model/"):
        os.makedirs(output_root + "/model/")
    if not os.path.isdir(output_root + "/metadata/"):
        os.makedirs(output_root + "/metadata/")

    # Load the best k models and the corresponding metadata
    models, metadatas = get_models_and_metadata(root + version_folder)

    # Load the validation subjects
    path = Path(data_root + "/imagesTr")
    subject_paths = list(path.glob("BRATS_*"))
    subjects = []

    for subject_path in subject_paths:
        label_path = change_img_to_label_path(subject_path)
        subject = tio.Subject({"MRI": tio.ScalarImage(subject_path),
                               "Label": tio.LabelMap(label_path)})
        subjects.append(subject)

    # Preprocess the validation data
    process = tio.Compose([
        tio.CropOrPad((240, 240, 155)),
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

        print(f"Evaluating model no. {index} for epoch {epoch}")

        # Load the patches from the current subject
        for subject_num in tqdm(range(len((val_dataset)))):
            grid_sampler = tio.inference.GridSampler(val_dataset[subject_num], 96, (8, 8, 8))
            aggregator = tio.inference.GridAggregator(grid_sampler)
            patch_loader = torch.utils.data.DataLoader(grid_sampler, batch_size=4)

            with torch.no_grad():
                for patches_batch in patch_loader:
                    input_tensor = patches_batch["MRI"]["data"].to(device)
                    locations = patches_batch[tio.LOCATION]
                    pred = model(input_tensor)
                    # We keep adding batches to the aggregator to later collect all the data.
                    aggregator.add_batch(pred, locations)

            pred = torch.swapaxes(F.one_hot(aggregator.get_output_tensor().argmax(0)).unsqueeze(dim=0), 0, 4).squeeze()
            label = torch.swapaxes(F.one_hot(val_dataset[0]["Label"].data.long()), 0, 4).squeeze()

            # If the first element is not a channel dimension, add that dimension.
            if pred.shape[0] > 6:
                pred = pred.unsqueeze(dim=0)

            # Extend the number of channels of the prediction to 4 if necessary.
            for it in range(pred.shape[0], label.shape[0]):
                pred = torch.cat((pred, torch.zeros_like(pred[0]).unsqueeze(0)), 0)

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

        # Visualize all of the losses for the specified slice indices.
        save_plots_for_index(preds[worst_index], worst_index, slices_to_show, output_root + "/images/",
                             f"epoch={epoch}-perc=0",
                             f"0th percentile, loss={worst_loss * 100:.2f}%")

        save_plots_for_index(preds[perc_25_index], perc_25_index, slices_to_show, output_root + "/images/",
                             f"epoch={epoch}-perc=25",
                             f"25th percentile, loss={perc_25_loss * 100:.2f}%")

        save_plots_for_index(preds[median_index], median_index, slices_to_show, output_root + "/images/",
                             f"epoch={epoch}-perc=50",
                             f"50th percentile, loss={median_loss * 100:.2f}%")

        save_plots_for_index(preds[perc_75_index], perc_75_index, slices_to_show, output_root + "/images/",
                             f"epoch={epoch}-perc=75",
                             f"75th percentile, loss={perc_75_loss * 100:.2f}%")

        save_plots_for_index(preds[best_index], best_index, slices_to_show, output_root + "/images/",
                             f"epoch={epoch}-perc=100",
                             f"100th percentile, loss={best_loss * 100:.2f}%")

    print(sorted(loss_per_model))


if __name__ == "__main__":
    main()