from argparse import Namespace, ArgumentParser
from pathlib import Path

import re
import os
import torchio as tio
import torch
import pytorch_lightning as pl
from pytorch_lightning.callbacks import ModelCheckpoint
from pytorch_lightning.loggers import TensorBoardLogger

from model import UNet
from segmenter import Segmenter


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
    # IO parameters
    parser.add_argument("--root-path", dest="root_path", default="Preprocessed/",
                        help="The directory where the training and label data are located."
                             "It is assumed that the training data can be found under 'imagesTr/' and the label"
                             "data can be found under 'labelsTr/' as NIFTI files.")
    parser.add_argument("--device", dest="device", default="auto",
                        help="Which device to use, e.g., 'cpu' or 'gpu'. "
                             "Full list: https://lightning.ai/docs/pytorch/stable/extensions/accelerator.html")
    parser.add_argument("--output-path", dest="output_path", default="logs",
                        help="The output directory for the model checkpoints.")
    parser.add_argument("--out-channels", dest="out_channels", default="4",
                        help="The number of output channels of the network. There is one channel for the classification"
                             " 'no tumor' and one for each tumor tissue type.")
    parser.add_argument("--num-data-loader-workers", dest="num_data_loader_workers", default="0",
                        help="The number of workers for the data loaders, i.e., the training and validation data "
                             "loaders.")
    parser.add_argument("--keep-top-k-checkpoints", dest="keep_top_k_checkpoints", default="3",
                        help="The best k number of Lightning checkpoints to keep according to the tracked validation "
                             "loss.")
    parser.add_argument("--input-checkpoint", dest="input_checkpoint",
                        help="This is an optional argument that can be given if the user wants to use an existing"
                             " checkpoint to initialize the weights of the model. The input checkpoint's hyperparameters"
                             " will be ignored and only the learnable parameters of the checkpoint will be used."
                             " Thus, all the given hyperparameters are still relevant and overwrite any hyperparameters"
                             " defined in the input checkpoint. The hyperparameters reported in the new checkpoint"
                             " will also be the ones given as hyperparameters during this call. It has to be ensured"
                             " that the checkpoint is compatible with the current version of the Segmenter/Unet class."
                             " A .ckpt file is expected as input.")

    # Hyperparameters
    parser.add_argument("--batch-size", dest="batch_size", default="4",
                        help="The number of elements to train with per batch (with or without quotation marks).")
    parser.add_argument("--epochs", dest="num_epochs", default="30",
                        help="The number of epochs to train for (with or without quotation marks).")
    parser.add_argument("--kernel-size", dest="kernel_size", default="3",
                        help="The kernel size to use in the double-convolutions of the UNet. Must be odd.")
    parser.add_argument("--activation-fn", dest="activation_fn", default="ReLU()",
                        help="The activation function to use in the double-convolutions of the UNet. Must be "
                             "one of those listed here: https://pytorch.org/docs/stable/nn.html#non-linear"
                             "-activations-weighted-sum-nonlinearity,"
                             " spelled in the same way, e.g., 'ReLU()' or 'LeakyReLU(0.1)'.")
    parser.add_argument("--learning-rate", dest="learning_rate", default="1e-4",
                        help="The starting learning rate of the model. The learning  rate will decay exponentially every"
                             " epoch by multiplying the current learning rate of an epoch by --learning-rate-decay.")
    parser.add_argument("--learning-rate-decay", dest="learning_rate_decay", default="0.95",
                        help="The value by which the learning rate of the current epoch is multiplied, starting with"
                             " the value --learning-rate. So we implement an exponentially decreasing learning rate.")
    parser.add_argument("--dropout-probability", dest="dropout_probability", default="0",
                        help="The probability of applying dropout elementwise. Dropout will be applied after every"
                             " double-convolution layer")
    parser.add_argument("--test-split-percent", dest="test_split_percent", default="85",
                        help="The percentage of subjects to use for training. 1 - test_split_percent / 100 will be used"
                             " for validation.")
    parser.add_argument("--label-sample-prob", dest="label_sample_prob", default="0.4,0.3,0.2,0.1",
                        help="A list of the probabilities that the center of a patch should be one of the pixels"
                             " with that label. Index i in the list corresponds to the probability for label i. The"
                             " probabilities should be separated by commas, e.g., '0.1,0.2,0.3,0.4'.")
    parser.add_argument("--patch-size", dest="patch_size", default="96",
                        help="The size of the generated patches in pixels for each dimension.")
    parser.add_argument("--samples-per-volume", dest="samples_per_volume", default="5",
                        help="The chosen number of samples per volume per epoch.")
    parser.add_argument("--dice-loss-weights", dest="dice_loss_weights",
                        help="The weighing of the output classes 0 to 3 in the dice entropy loss. By default,"
                             " they are equally weighted. The weights should be separated by commas, e.g., "
                             "'0.1,0.2,0.3,0.4', but don't have to add up to 1.")
    parser.add_argument("--use-batch-norm", dest="use_batch_norm", default=False,
                        action="store_true",
                        help="Whether to use batch normalization after every convolutional layer.")
    args = parser.parse_args()

    return args


def parse_sample_tensor(s: str) -> torch.Tensor:
    """From a comma-separated list of values, get a corresponding tensor with the elements."""
    elements: list = [float(num) for num in s.split(",")]
    return torch.tensor(elements)


def main():
    # ----------- Reading hyperparameters

    # Fetch CMD arguments, including hyperparameters like the batch size.
    cmd_args: Namespace = get_cmd_args()

    # CMD parameters
    root_path = Path(cmd_args.root_path)
    device = cmd_args.device
    trainer_device_name = cmd_args.device.split(":")[0]
    device_index = 0
    if len(cmd_args.device.split(":")) == 2:
        device_index = int(cmd_args.device.split(":")[1])
    output_path = cmd_args.output_path

    # Hyperparameters
    batch_size = int(cmd_args.batch_size)
    num_epochs = int(cmd_args.num_epochs)
    kernel_size = int(cmd_args.kernel_size)
    learning_rate = float(cmd_args.learning_rate)
    learning_rate_decay = float(cmd_args.learning_rate_decay)
    dropout_probability = float(cmd_args.dropout_probability)

    activation_fn_str = "torch.nn." + cmd_args.activation_fn
    activation_fn: torch.nn.Module = eval(activation_fn_str)
    out_channels: int = int(cmd_args.out_channels)
    test_split: float = float(cmd_args.test_split_percent) / 100
    patch_size: int = int(cmd_args.patch_size)
    samples_per_volume: int = int(cmd_args.samples_per_volume)
    use_batch_norm: bool = bool(cmd_args.use_batch_norm)
    input_checkpoint: str = cmd_args.input_checkpoint
    num_data_loader_workers: int = int(cmd_args.num_data_loader_workers)
    keep_top_k_checkpoints: int = int(cmd_args.keep_top_k_checkpoints)

    label_sample_prob: dict = parse_sample_dict(cmd_args.label_sample_prob)
    dice_loss_weights: torch.Tensor = None
    if cmd_args.dice_loss_weights is not None:
        dice_loss_weights = parse_sample_tensor(cmd_args.dice_loss_weights).to(device)
    print("Dice loss weights:", dice_loss_weights)

    # ----------- Preprocessing

    # Read in the raw data, not the preprocessed data. The preprocessing takes place in this file.
    path = root_path / Path("imagesTr/")
    subject_paths = list(path.glob("BRATS_*"))
    # Sort these because Linux is stupid
    subject_paths = sorted(subject_paths, key=lambda x: int(re.findall(r'\d+', str(os.path.basename(x)))[0]))
    subjects = []

    num_train_elements = int(test_split * len(subject_paths))
    print("Num train elements:", num_train_elements)

    # The subjects are tio objects containing the MRI scan and the label.
    for subject_path in subject_paths:
        label_path = change_img_to_label_path(subject_path)
        subject = tio.Subject({"MRI": tio.ScalarImage(subject_path),
                               "Label": tio.LabelMap(label_path)})
        subjects.append(subject)

    for index, subject in enumerate(subjects[:num_train_elements]):
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
    augmentation_gamma = tio.RandomGamma(log_gamma=(-0.3, 0.3))

    # The validation only gets the preprocessed data, whereas we create new images for the test data in the form of
    # augmented data with the above transformations.
    val_transform = process
    train_transform = tio.Compose([process, augmentation_affine, augmentation_gamma])

    # This is the train/test split:
    print(f"Training: {num_train_elements / len(subject_paths):.4f}, "
          f"val: {1 - num_train_elements / len(subject_paths):.4f}")

    train_dataset = tio.SubjectsDataset(subjects[:num_train_elements], transform=train_transform)
    val_dataset = tio.SubjectsDataset(subjects[num_train_elements:], transform=val_transform)

    # The sampler decides with what probability each label should occur in the training. This allows us to oversample
    # the tumors by assigning the tumor label a higher probability. Specifically, background (label 0) has probability
    # 0.2, liver (label 1) has probability 0.3, and tumor (label 2) has probability 0.5. The probabilities refer
    # to how likely it is that the corresponding label is in the middle of the patch.
    sampler = tio.data.LabelSampler(patch_size=patch_size, label_name="Label",
                                    label_probabilities=label_sample_prob)

    # This is the queue that generates the actual patches from the images. The values max_length and num_workers
    # can be very memory-consuming and therefore have to be adapted to the specific hardware you're running this code
    # on.
    train_patches_queue = tio.Queue(
        train_dataset,
        max_length=samples_per_volume,
        samples_per_volume=samples_per_volume,
        sampler=sampler,
        num_workers=0
    )

    val_patches_queue = tio.Queue(
        val_dataset,
        max_length=samples_per_volume,
        samples_per_volume=samples_per_volume,
        sampler=sampler,
        num_workers=0
    )

    # ----------- Data loading and training
    train_loader = torch.utils.data.DataLoader(train_patches_queue, batch_size=batch_size, num_workers=num_data_loader_workers,
                                               pin_memory=True)
    val_loader = torch.utils.data.DataLoader(val_patches_queue, batch_size=batch_size, num_workers=num_data_loader_workers,
                                             pin_memory=True)

    in_channels = train_dataset[0]["MRI"].shape[0]

    model = Segmenter(in_channels=in_channels, out_channels=out_channels,
                      odd_kernel_size=kernel_size, activation_fn=activation_fn, learning_rate=learning_rate,
                      learning_rate_decay=learning_rate_decay, dropout_probability=dropout_probability,
                      batch_size=batch_size, label_probabilities=label_sample_prob, patch_size=patch_size,
                      samples_per_volume=samples_per_volume, dice_loss_weights=dice_loss_weights,
                      use_batch_norm=use_batch_norm)

    # Initialize the model's weights from the given checkpoint (if one was given).
    if input_checkpoint is not None:
        try:
            input_model = Segmenter.load_from_checkpoint(input_checkpoint)
            input_state_dict = input_model.state_dict()
            model.load_state_dict(input_state_dict)
            print(f"Using weight initialization from checkpoint {input_checkpoint}")
        except Exception as e:
            print(e)
            print(f"The input checkpoint {input_checkpoint} couldn't be loaded. Check if the Segmenter class and"
                  f" the checkpoint are compatible.")
    else:
        print("Using default weight initialization")

    print("Hyperparameters:")
    print(model.hparams)

    checkpoint_callback = ModelCheckpoint(
        monitor="Val loss",
        save_top_k=keep_top_k_checkpoints,
        mode="min"
    )

    print("Top k:", checkpoint_callback.save_top_k)

    print("\n\n------------------Our model:\n")
    print(model)
    print("Number of parameters:", sum(param.numel() for param in model.parameters()))

    trainer = pl.Trainer(devices=[device_index], accelerator=trainer_device_name,
                         logger=TensorBoardLogger(save_dir=output_path),
                         log_every_n_steps=1,
                         callbacks=[checkpoint_callback], max_epochs=num_epochs,
                         gradient_clip_val=100*learning_rate, gradient_clip_algorithm="value")

    print(f"Starting training with {num_epochs} epochs...")
    trainer.fit(model, train_loader, val_loader)

if __name__ == "__main__":
    main()
