from pathlib import Path

import torch
import pytorch_lightning as pl
from pytorch_lightning.callbacks import ModelCheckpoint
from pytorch_lightning.loggers import TensorBoardLogger
import imgaug.augmenters as iaa

from dataset import TumorDataset
from brain_tumor_segmentation import BrainTumorSegmentation
from argparse import ArgumentParser, Namespace

activation_functions = {
    'relu': torch.nn.ReLU(),
    'leakyrelu': torch.nn.LeakyReLU(),
    'prelu': torch.nn.PReLU(),
    'elu': torch.nn.ELU(),
    'selu': torch.nn.SELU(),
    'celu': torch.nn.CELU(),
    'gelu': torch.nn.GELU(),
    'sigmoid': torch.nn.Sigmoid(),
    'tanh': torch.nn.Tanh(),
    'hardtanh': torch.nn.Hardtanh(),
    'softplus': torch.nn.Softplus(),
    'softshrink': torch.nn.Softshrink(),
    'softsign': torch.nn.Softsign(),
    'softmax': torch.nn.Softmax(),
    'logsoftmax': torch.nn.LogSoftmax(),
    'hardsigmoid': torch.nn.Hardsigmoid(),
    'hardswish': torch.nn.Hardswish(),
    'silu': torch.nn.SiLU(),
    'mish': torch.nn.Mish(),
    'tanhshrink': torch.nn.Tanhshrink(),
    'glu': torch.nn.GLU(),
    'rrelu': torch.nn.RReLU(),
}

# Augmentation Pipeline
seq = iaa.Sequential([
    iaa.Affine(scale=(0.85, 1.15), # Zoom in or out
               rotate=(-45, 45)),  # Rotate up to 45 degrees
    iaa.ElasticTransformation()  # Random Elastic Deformations
])

# Example: python train.py --train-path ../Preprocessed/train --val_path ../Preprocessed/val --device "gpu" --batch-size 8 --epochs 35 --output-dir "../logs"
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
    parser.add_argument("--batch-size", dest="batch_size", default="32",
                        help="The number of elements to train with per batch (with or without quotation marks).")
    parser.add_argument("--epochs", dest="num_epochs", default="20",
                        help="The number of epochs to train for (with or without quotation marks).")
    parser.add_argument("--output-dir", dest="output_dir", default="logs",
                        help="The output directory for the model checkpoints.")
    parser.add_argument("--kernel-size", dest="kernel_size", default="3",
                        help="The kernel size to use in the double-convolutions of the UNet. Must be odd.")
    parser.add_argument("--learning-rate", dest="learning_rate", default="1e-5",
                        help="The learning rate of the model.")
    parser.add_argument("--activation-fn", dest="activation_fn", default="ReLU()",
                        help="The activation function to use in the double-convolutions of the UNet. Must be "
                             "one of those listed here: https://pytorch.org/docs/stable/nn.html#non-linear"
                             "-activations-weighted-sum-nonlinearity,"
                             "spelled in the same way, e.g., 'ReLU()' or 'LeakyReLU(0.1)'.")
    args = parser.parse_args()

    return args

def main():

    # Fetch CMD arguments, including hyperparameters like the batch size.
    cmd_args: Namespace = get_cmd_args()

    # CMD parameters
    train_path = Path(cmd_args.train_path)
    val_path = Path(cmd_args.val_path)
    device = cmd_args.device
    learning_rate = float(cmd_args.learning_rate)

    # Hyperparameters
    batch_size = int(cmd_args.batch_size)
    num_epochs = int(cmd_args.num_epochs)
    kernel_size = int(cmd_args.kernel_size)

    activation_fn_str = "torch.nn." + cmd_args.activation_fn
    activation_fn: torch.nn.Module = eval(activation_fn_str)

    # Data loaders
    # Don't augment the data for now
    # TODO Add the augmentation back for the training data!
    train_dataset = TumorDataset(train_path, None)
    val_dataset = TumorDataset(val_path, None)


    # Dataloader
    num_workers = 2

    train_loader = torch.utils.data.DataLoader(train_dataset, batch_size=batch_size, num_workers=num_workers,
                                               shuffle=True, persistent_workers=True, pin_memory=True, prefetch_factor=2)
    val_loader = torch.utils.data.DataLoader(val_dataset, batch_size=batch_size, num_workers=num_workers, shuffle=False,
                                             persistent_workers=True, pin_memory=True, prefetch_factor=2)

    # A specific seed to make the results reproducible.
    # torch.manual_seed(0)
    # Without loss of generality, determine the number of input and output channels using the first image and
    # label, respectively. Within the first image, the dimensions are as follows: (batch_size, number channels, width,
    # height). So the first dimension (0-indexed) contains the respective number of channels. This automatic
    # inference of channels is useful, because the user doesn't have to bother with them and the model can therefore
    # adapt dynamically.
    first_img, first_label = train_dataset[0]
    input_channels = first_img.shape[0]
    output_channels = first_label.shape[0]
    all_channels = train_dataset
    model = BrainTumorSegmentation(in_channels=input_channels, out_channels=output_channels, odd_kernel_size=kernel_size,
                                   learning_rate=learning_rate, activation_fn=activation_fn)

    # This is for setting regular checkpoints to reconstruct the model.
    checkpoint_callback = ModelCheckpoint(monitor="Val loss", save_top_k=10, mode="min")
    trainer = pl.Trainer(devices=[0], accelerator=device, logger=TensorBoardLogger(save_dir="logs"),
                         log_every_n_steps=1, callbacks=checkpoint_callback, max_epochs=num_epochs)

    print("------------ OUR MODEL: ------------")
    print(model)

    trainer.fit(model, train_loader, val_loader)

# Training
if __name__ == '__main__':
    main()
