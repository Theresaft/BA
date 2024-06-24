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


def parse_sample_dict(s: str) -> dict[int, float]:
    lst = [float(val) for val in s.split(",")]
    return {i: lst[i] for i in range(len(lst))}


def get_cmd_args() -> Namespace:
    parser = ArgumentParser()
    parser.add_argument("--root-path", dest="root_path", default="Preprocessed/",
                        help="The directory where the training and label data are located."
                             "It is assumed that the training data can be found under 'imagesTr/' and the label"
                             "data can be found under 'labelsTr/' as NIFTI files.")
    parser.add_argument("--device", dest="device", default="auto",
                        choices=["auto", "cpu", "gpu", "cuda", "mps", "tpu"],
                        help="Which device to use, e.g., 'cpu' or 'gpu'. "
                             "Full list: https://lightning.ai/docs/pytorch/stable/extensions/accelerator.html")
    parser.add_argument("--batch-size", dest="batch_size", default="4",
                        help="The number of elements to train with per batch (with or without quotation marks).")
    parser.add_argument("--epochs", dest="num_epochs", default="30",
                        help="The number of epochs to train for (with or without quotation marks).")
    parser.add_argument("--output-path", dest="output_path", default="logs",
                        help="The output directory for the model checkpoints.")
    parser.add_argument("--kernel-size", dest="kernel_size", default="3",
                        help="The kernel size to use in the double-convolutions of the UNet. Must be odd.")
    parser.add_argument("--activation-fn", dest="activation_fn", default="ReLU()",
                        help="The activation function to use in the double-convolutions of the UNet. Must be "
                             "one of those listed here: https://pytorch.org/docs/stable/nn.html#non-linear"
                             "-activations-weighted-sum-nonlinearity,"
                             "spelled in the same way, e.g., 'ReLU()' or 'LeakyReLU(0.1)'.")
    parser.add_argument("--out-channels", dest="out_channels", default="4",
                        help="The number of output channels of the network. There is one channel for the classification"
                             " 'no tumor' and one for each tumor tissue type.")
    parser.add_argument("--learning-rate", dest="learning_rate", default="1e-4",
                        help="The learning rate of the model.")
    parser.add_argument("--test-split-percent", dest="test_split_percent", default="85",
                        help="The percentage of subjects to use for training. 1 - test_split_percent / 100 will be used"
                             " for validation.")
    parser.add_argument("--label-sample-prob", dest="label_sample_prob", default="0.4,0.3,0.2,0.1",
                        help="A list of the probabilities that the center of a patch should be one of the pixels"
                             "with that label. Index i in the list corresponds to the probability for label i. The"
                             " probabilities should be separated by commas, e.g., '0.1,0.2,0.3,0.4'.")
    args = parser.parse_args()

    return args


def main():
    # ----------- Reading hyperparameters

    # Fetch CMD arguments, including hyperparameters like the batch size.
    cmd_args: Namespace = get_cmd_args()

    # CMD parameters
    root_path = Path(cmd_args.root_path)
    device = cmd_args.device
    output_path = cmd_args.output_path

    # Hyperparameters
    batch_size = int(cmd_args.batch_size)
    num_epochs = int(cmd_args.num_epochs)
    kernel_size = int(cmd_args.kernel_size)
    learning_rate = float(cmd_args.learning_rate)

    activation_fn_str = "torch.nn." + cmd_args.activation_fn
    activation_fn: torch.nn.Module = eval(activation_fn_str)
    out_channels: int = int(cmd_args.out_channels)
    test_split: float = float(cmd_args.test_split_percent) / 100

    label_sample_prob: dict = parse_sample_dict(cmd_args.label_sample_prob)
    print(f"Label probabilities: {label_sample_prob}")

    # ----------- Preprocessing

    # Read in the raw data, not the preprocessed data. The preprocessing takes place in this file.
    path = root_path / Path("imagesTr/")
    subject_paths = list(path.glob("BRATS_*"))
    subjects = []

    num_train_elements = int(test_split * len(subject_paths))
    print("Num train elements:", num_train_elements)

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

    # The augmentation creates new images elastic deformations, followed by affine transformations in the form of
    # scaling, rotation, and translation. The translation is only within slices, not in the z direction.
    # augmentation_elastic = tio.RandomElasticDeformation(num_control_points=10)
    augmentation_affine = tio.RandomAffine(scales=(0.85, 1.15), degrees=(-25, 25), translation=(-20, 20, -20, 20, 0, 0))

    # The validation only gets the preprocessed data, whereas we create new images for the test data in the form of
    # augmented data with the above transformations.
    val_transform = process
    train_transform = tio.Compose([process, augmentation_affine])

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
                                    label_probabilities=label_sample_prob)

    # This is the queue that generates the actual patches from the images. The values max_length and num_workers
    # can be very memory-consuming and therefore have to be adapted to the specific hardware you're running this code
    # on.
    train_patches_queue = tio.Queue(
        train_dataset,
        max_length=50,
        samples_per_volume=5,
        sampler=sampler,
        num_workers=4
    )

    val_patches_queue = tio.Queue(
        val_dataset,
        max_length=50,
        samples_per_volume=5,
        sampler=sampler,
        num_workers=4
    )

    # ----------- Data loading and training
    train_loader = torch.utils.data.DataLoader(train_patches_queue, batch_size=batch_size, num_workers=0,
                                               pin_memory=True)
    val_loader = torch.utils.data.DataLoader(val_patches_queue, batch_size=batch_size, num_workers=0,
                                             pin_memory=True)

    in_channels = train_dataset[0]["MRI"].shape[0]

    model = Segmenter(in_channels=in_channels, out_channels=out_channels,
                      odd_kernel_size=kernel_size, activation_fn=activation_fn, learning_rate=learning_rate,
                      batch_size=batch_size)

    checkpoint_callback = ModelCheckpoint(
        monitor="Val loss",
        save_top_k=10,
        mode="min"
    )

    print("\n\n------------------Our model:\n")
    print(model)

    trainer = pl.Trainer(devices=[0], accelerator=device,
                         logger=TensorBoardLogger(save_dir=output_path),
                         log_every_n_steps=1,
                         callbacks=[checkpoint_callback], max_epochs=num_epochs)

    trainer.fit(model, train_loader, val_loader)


if __name__ == "__main__":
    main()
