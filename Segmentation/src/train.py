from pathlib import Path

import torch
import pytorch_lightning as pl
from pytorch_lightning.callbacks import ModelCheckpoint
from pytorch_lightning.loggers import TensorBoardLogger
import imgaug.augmenters as iaa

from dataset import TumorDataset
from brain_tumor_segmentation import BrainTumorSegmentation
from argparse import ArgumentParser, Namespace

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
    # TODO More hyperparameters: Kernel size, channel sizes per layer, activation function
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

    # Data loaders
    train_dataset = TumorDataset(train_path, seq)  # Only the training dataset is augmented
    val_dataset = TumorDataset(val_path, None)

    # Dataloader
    num_workers = 8

    train_loader = torch.utils.data.DataLoader(train_dataset, batch_size=batch_size, num_workers=num_workers,
                                               shuffle=True, persistent_workers=True, pin_memory=True, prefetch_factor=4)
    val_loader = torch.utils.data.DataLoader(val_dataset, batch_size=batch_size, num_workers=num_workers, shuffle=False,
                                             persistent_workers=True, pin_memory=True, prefetch_factor=4)

    # A specific seed to make the results reproducible.
    torch.manual_seed(0)
    model = BrainTumorSegmentation()

    # This is for setting regular checkpoints to reconstruct the model.
    checkpoint_callback = ModelCheckpoint(monitor="Val Dice", save_top_k=10, mode="min")
    trainer = pl.Trainer(devices=[0], accelerator=device, logger=TensorBoardLogger(save_dir="logs"),
                         log_every_n_steps=1, callbacks=checkpoint_callback, max_epochs=num_epochs)

    print("------------ OUR MODEL: ------------")
    print(model)

    trainer.fit(model, train_loader, val_loader)


# Training
if __name__ == '__main__':
    main()
