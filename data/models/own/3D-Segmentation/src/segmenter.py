import torch
from model import UNet
import torch
import pytorch_lightning as pl
import torch.nn.functional as F
from dice_loss import DiceLoss


class Segmenter(pl.LightningModule):

    dice_losses_cur_epoch_train = None
    dice_losses_cur_epoch_validation = None
    train_iterations = 0
    val_iterations = 0

    def __init__(self, in_channels: int, out_channels: int, odd_kernel_size: int, activation_fn: torch.nn.Module,
                 learning_rate: float, learning_rate_decay: float, dropout_probability: float, batch_size: int,
                 label_probabilities: dict, patch_size: int, samples_per_volume: int, dice_loss_weights = None,
                 use_batch_norm: bool = False):
        super().__init__()
        self.save_hyperparameters()
        self.model = UNet(in_channels=in_channels, out_channels=out_channels,
                          odd_kernel_size=odd_kernel_size, activation_fn=activation_fn,
                          dropout_probability=dropout_probability, use_batch_norm=use_batch_norm)
        self.optimizer = torch.optim.Adam(self.model.parameters(), lr=learning_rate)
        self.scheduler = torch.optim.lr_scheduler.ExponentialLR(self.optimizer, gamma=learning_rate_decay)
        self.dice_loss_weights = dice_loss_weights
        # As suggested in "Focal Loss for Dense Object Detection" (in 3.1), we use heuristically determined label
        # probabilities to manually weigh the cross entropy weights. This is necessary because the classes have
        # very different probabilities and a cross entropy loss that doesn't reflect that seems to run into a local
        # minimum quickly in which nothing gets segmented at all because that delivers a decent accuracy by itself.
        # These are the label probabilities for the training data:
        # {0: 0.9885378077335636, 1: 0.007319072994880918, 2: 0.002065825332042662, 3: 0.0020772939395128586}
        # This gives us the following approximate inverted values as weights: 0: 1, 1: 137, 2: 484, 3: 481
        self.loss_fn = DiceLoss(self.dice_loss_weights)
        self.batch_size = batch_size
        self.label_probabilities = label_probabilities
        self.patch_size = patch_size
        self.samples_per_volume = samples_per_volume
        self.use_batch_norm = use_batch_norm

        # These are not hyperparameters
        self.dice_losses_cur_epoch_train = torch.zeros_like(dice_loss_weights)
        self.dice_losses_cur_epoch_validation = torch.zeros_like(dice_loss_weights)

    def forward(self, x):
        return self.model(x)

    def training_step(self, batch, batch_idx):
        # This is the CT scan. In torchio, the batch objects doesn't only contain the core volume data, but also
        # some metadata. Hence, we need to extract its data attribute.
        img = batch["MRI"]["data"]
        # In order to use cross-entropy loss, we need to remove the channel dimension. TODO Why??
        # We perform one-hot encoding on the target, but not on the prediction because that is the format
        # that CrossEntropyLoss expects.
        mask = batch["Label"]["data"].squeeze().long()

        pred = self(img)
        loss = self.loss_fn(pred, mask)
        self.dice_losses_cur_epoch_train += self.loss_fn.current_loss
        self.train_iterations += 1

        self.log("Train loss", loss, batch_size=self.batch_size)
        return loss

    def validation_step(self, batch, batch_idx):
        # This is the CT scan. In torchio, the batch objects doesn't only contain the core volume data, but also
        # some metadata. Hence, we need to extract its data attribute.
        img = batch["MRI"]["data"]
        # In order to use cross-entropy loss, we need to remove the channel dimension. TODO Why??
        mask = batch["Label"]["data"].squeeze().long()

        pred = self(img)
        loss = self.loss_fn(pred, mask)
        self.dice_losses_cur_epoch_validation += self.loss_fn.current_loss
        self.val_iterations += 1

        self.log("Val loss", loss, batch_size=self.batch_size)
        return loss

    def configure_optimizers(self):
        return {"optimizer": self.optimizer, "lr_scheduler": self.scheduler}

    def on_train_epoch_end(self):
        num_batches = self.train_iterations
        average_losses = self.dice_losses_cur_epoch_train / num_batches
        print(f"\nAverage training loss for epoch {self.trainer.current_epoch} per channel: "
              f"{torch.Tensor.cpu(average_losses)}")
        print(f"Average training loss for epoch {self.trainer.current_epoch}: "
              f"{(torch.Tensor.cpu(average_losses).mean().item()) * 100:.2f}%", end="\n\n")
        self.dice_losses_cur_epoch_train = torch.zeros_like(self.dice_loss_weights)
        self.train_iterations = 0

    def on_validation_epoch_end(self):
        num_batches = self.val_iterations
        average_losses = self.dice_losses_cur_epoch_validation / num_batches
        print(f"\nAverage validation loss for epoch {self.trainer.current_epoch} per channel: "
              f"{torch.Tensor.cpu(average_losses)}")
        print(f"Average validation loss for epoch {self.trainer.current_epoch}: "
              f"{(torch.Tensor.cpu(average_losses).mean().item()) * 100:.2f}%", end="\n\n")
        self.dice_losses_cur_epoch_validation = torch.zeros_like(self.dice_loss_weights)
        self.val_iterations = 0

    def _output_gradients(self):
        min_grad = float("inf")
        max_grad = float("-inf")
        param_sum = 0
        param_count = 0
        for param in self.parameters():
            if param.grad is not None:
                param_sum += param.grad.sum().item()
                param_count += param.grad.numel()
                min_grad = min(min_grad, param.grad.min().item())
                max_grad = max(max_grad, param.grad.max().item())

        if param_count != 0:
            print("Grad:\t\t", "avg:", param_sum / param_count, ", min:", min_grad, ", max:", max_grad)
