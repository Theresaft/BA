import torch
from model import UNet
import torch
import pytorch_lightning as pl


class Segmenter(pl.LightningModule):
    def __init__(self, in_channels: int, out_channels: int, odd_kernel_size: int, activation_fn: torch.nn.Module,
                 learning_rate: float):
        super().__init__()
        self.save_hyperparameters()
        self.model = UNet(in_channels=in_channels, out_channels=out_channels,
                          odd_kernel_size=odd_kernel_size, activation_fn=activation_fn)
        self.optimizer = torch.optim.Adam(self.model.parameters(), lr=learning_rate)
        self.loss_fn = torch.nn.CrossEntropyLoss()

    def forward(self, x):
        return self.model(x)

    def training_step(self, batch, batch_idx):
        # This is the CT scan. In torchio, the batch objects doesn't only contain the core volume data, but also
        # some metadata. Hence, we need to extract its data attribute.
        img = batch["MRI"]["data"]
        # In order to use cross-entropy loss, we need to remove the channel dimension. TODO Why??
        mask = batch["Label"]["data"][:, 0]
        mask = mask.long()

        pred = self(img)
        print(f"img: {img.shape}")
        print(f"mask: {mask.shape}")
        print(f"other: {batch['Label']['data'].shape}")
        loss = self.loss_fn(pred, mask)
        self.log("Train loss", loss)
        return loss

    def validation_step(self, batch, batch_idx):
        # This is the CT scan. In torchio, the batch objects doesn't only contain the core volume data, but also
        # some metadata. Hence, we need to extract its data attribute.
        img = batch["MRI"]["data"]
        # In order to use cross-entropy loss, we need to remove the channel dimension. TODO Why??
        mask = batch["Label"]["data"][:, 0]
        mask = mask.long()

        pred = self(img)
        loss = self.loss_fn(pred, mask)
        self.log("Val loss", loss)
        return loss

    def configure_optimizers(self):
        return [self.optimizer]
