import torch
from model import UNet
import torch
import pytorch_lightning as pl


class Segmenter(pl.LightningModule):
    def __init__(self, in_channels: int, out_channels: int, odd_kernel_size: int, activation_fn: torch.nn.Module,
                 learning_rate: float, learning_rate_decay: float, dropout_probability: float, batch_size: int,
                 label_probabilities: dict, patch_size: int, samples_per_volume: int):
        super().__init__()
        self.save_hyperparameters()
        self.model = UNet(in_channels=in_channels, out_channels=out_channels,
                          odd_kernel_size=odd_kernel_size, activation_fn=activation_fn,
                          dropout_probability=dropout_probability)
        self.optimizer = torch.optim.Adam(self.model.parameters(), lr=learning_rate)
        self.scheduler = torch.optim.lr_scheduler.ExponentialLR(self.optimizer, gamma=learning_rate_decay)
        self.loss_fn = torch.nn.CrossEntropyLoss()
        self.batch_size = batch_size
        self.label_probabilities = label_probabilities
        self.patch_size = patch_size
        self.samples_per_volume = samples_per_volume

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
        loss = self.loss_fn(pred, mask)
        self.log("Train loss", loss, batch_size=self.batch_size)
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
        self.log("Val loss", loss, batch_size=self.batch_size)
        return loss

    def configure_optimizers(self):
        return {"optimizer": self.optimizer, "lr_scheduler": self.scheduler}

    def on_train_epoch_start(self):
        lr = self.optimizer.param_groups[0]["lr"]
        print(f"\nCurrent learning rate: {lr}")
