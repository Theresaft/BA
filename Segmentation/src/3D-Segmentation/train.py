from argparse import Namespace, ArgumentParser
from pathlib import Path

import torchio as tio
import torch
import pytorch_lightning as pl
from pytorch_lightning.callbacks import ModelCheckpoint
from pytorch_lightning.loggers import TensorBoardLogger

from model import UNet
from segmenter import Segmenter


# TODO Change this function appropriately
def change_img_to_label_path(path):
    """ Returns all directories in a path. """
    parts = list(path.parts)
    # Replace path
    parts[parts.index("imagesTr")] = "labelsTr"
    return Path(*parts)

def get_cmd_args() -> Namespace:

    parser = ArgumentParser()
    parser.add_argument("--train-path", dest="train_path", default="Preprocessed/train",
                        help="The directory where the training data is located.")
    parser.add_argument("--val-path", dest="val_path", default="Preprocessed/val",
                        help="The directory where the validation data is located.")
    parser.add_argument("--device", dest="device", default="auto",
                        choices=["auto", "cpu", "gpu", "cuda", "mps", "tpu"],
                        help="Which device to use, e.g., 'cpu' or 'gpu'. "
                             "Full list: https://lightning.ai/docs/pytorch/stable/extensions/accelerator.html")
    parser.add_argument("--batch-size", dest="batch_size", default="4",
                        help="The number of elements to train with per batch (with or without quotation marks).")
    parser.add_argument("--epochs", dest="num_epochs", default="30",
                        help="The number of epochs to train for (with or without quotation marks).")
    parser.add_argument("--output-dir", dest="output_dir", default="logs",
                        help="The output directory for the model checkpoints.")
    parser.add_argument("--kernel-size", dest="kernel_size", default="3",
                        help="The kernel size to use in the double-convolutions of the UNet. Must be odd.")
    parser.add_argument("--activation-fn", dest="activation_fn", default="relu",
                        help="The activation function to use in the double-convolutions of the UNet. Must be "
                             "one of those listed here: https://pytorch.org/docs/stable/nn.html#non-linear"
                             "-activations-weighted-sum-nonlinearity,"
                             "in lowercase. For example, 'relu' corresponds to torch.nn.ReLU() and 'logsoftmax'"
                             "corresponds to torch.nn.LogSoftmax().")
    args = parser.parse_args()

    return args


def main():
    # Fetch CMD arguments, including hyperparameters like the batch size.
    cmd_args: Namespace = get_cmd_args()

    # CMD parameters
    train_path = Path(cmd_args.train_path)
    val_path = Path(cmd_args.val_path)
    device = cmd_args.device

    # Hyperparameters
    batch_size = int(cmd_args.batch_size)
    num_epochs = int(cmd_args.num_epochs)
    kernel_size = int(cmd_args.kernel_size)

    # ----------- Preprocessing

    num_train_elements = 400

    # Read in the raw data, not the preprocessed data. The preprocessing takes place in this file.
    path = Path("D:/Deep Learning/Task01_BrainTumour/imagesTr")
    subject_paths = list(path.glob("BRATS_*"))
    subjects = []

    # The subjects are tio objects containing the MRI scan and the label.
    for subject_path in subject_paths:
        label_path = change_img_to_label_path(subject_path)
        subject = tio.Subject({"MRI": tio.ScalarImage(subject_path),
                               "Label": tio.LabelMap(label_path)})
        subjects.append(subject)

    for subject in subjects:
        assert subject["MRI"].orientation == ("R", "A", "S")

    # The first step shouldn't change anything for the given brain tumor dataset, since the scans are all the
    # same size anyway. The second step replaces the normalization step of the 2D segmentation.
    process = tio.Compose([
        tio.CropOrPad((240, 240, 155)),
        tio.RescaleIntensity((-1, 1))
    ])

    # The augmentation creates new images with scales between 0.9 and 1.1 as well as rotating by between -10 degrees
    # and 10 degrees.
    augmentation = tio.RandomAffine(scales=(0.9, 1.1), degrees=(-25, 25))

    # The validation only gets the preprocessed data, whereas we create new images for the test data in the form of
    # augmented data with the above transformations.
    val_transform = process
    train_transform = tio.Compose([process, augmentation])

    # This is the train/test split:
    print(f"Training: {num_train_elements / len(subject_paths):.4f}, "
          f"val: {1 - num_train_elements / len(subject_paths):.4f}")

    train_dataset = tio.SubjectsDataset(subjects[:num_train_elements], transform=train_transform)
    val_dataset = tio.SubjectsDataset(subjects[num_train_elements:], transform=val_transform)

    # The sampler decides with what probability each label should occur in the training. This allows us to oversample
    # the tumors by assigning the tumor label a higher probability. Specifically, background (label 0) has probability
    # 0.2, liver (label 1) has probability 0.3, and tumor (label 2) has probability 0.5. The probabilities refer
    # to how likely it is that the corresponding label is in the middle of the patch.
    sampler = tio.data.LabelSampler(patch_size=96, label_name="Label",
                                    label_probabilities={0: 0.4, 1: 0.3, 2: 0.15, 3: 0.15})

    # This is the queue that generates the actual patches from the images. The values max_length and num_workers
    # can be very memory-consuming and therefore have to be adapted to the specific hardware you're running this code
    # on.
    train_patches_queue = tio.Queue(
        train_dataset,
        max_length=40,
        samples_per_volume=5,
        sampler=sampler,
        num_workers=4
    )

    val_patches_queue = tio.Queue(
        val_dataset,
        max_length=40,
        samples_per_volume=5,
        sampler=sampler,
        num_workers=4
    )

    # ----------- Data loading and training
    train_loader = torch.utils.data.DataLoader(train_patches_queue, batch_size=4, num_workers=0,
                                               pin_memory=True)
    val_loader = torch.utils.data.DataLoader(val_patches_queue, batch_size=4, num_workers=0,
                                             pin_memory=True)

    model = Segmenter()
    checkpoint_callback = ModelCheckpoint(
        monitor="Val loss",
        save_top_k=10,
        mode="min"
    )

    print("Our model:")
    print(model)

    trainer = pl.Trainer(devices=[0], accelerator="cuda",
                         logger=TensorBoardLogger(save_dir="logs"),
                         log_every_n_steps=1,
                         callbacks=[checkpoint_callback], max_epochs=10)
    trainer.fit(model, train_loader, val_loader)


if __name__ == "__main__":
    main()
