import torch
import pytorch_lightning as pl
from model import UNet
from dice_loss import DiceLoss


class BrainTumorSegmentation(pl.LightningModule):
    def __init__(self, in_channels: int, out_channels: int, odd_kernel_size: int, learning_rate: float,
                 activation_fn: torch.nn.Module):
        super().__init__()

        self.model = UNet(in_channels, out_channels, odd_kernel_size, activation_fn)

        self.optimizer = torch.optim.Adam(self.model.parameters(), lr=learning_rate)
        self.loss_fn = DiceLoss()
        self.previous_pred = torch.tensor([0, 0, 0, 0.])

    def forward(self, data):
        return torch.softmax(self.model(data), dim=1)

    def training_step(self, batch, batch_idx):
        mri, mask = batch
        mask = mask.float()  # real segmentation
        pred = self(mri)  # predicted segmentation
        loss = self.loss_fn(pred, mask)

        self.log("Training loss", loss)
        return loss

    def validation_step(self, batch, batch_idx):
        mri, mask = batch
        mask = mask.float()  # real segmentation
        pred = self(mri)  # predicted segmentation

        loss = self.loss_fn(pred, mask)

        self.log("Val loss", loss)
        return loss

    def configure_optimizers(self):
        return [self.optimizer]