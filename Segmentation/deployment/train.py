from pathlib import Path

import torch
import pytorch_lightning as pl
from pytorch_lightning.callbacks import ModelCheckpoint
from pytorch_lightning.loggers import TensorBoardLogger
import imgaug.augmenters as iaa

from dataset import CardiacDataset
from model import UNet

# Augmentation Pipeline
seq = iaa.Sequential([
    iaa.Affine(scale=(0.85, 1.15), # Zoom in or out
               rotate=(-45, 45)),  # Rotate up to 45 degrees
    iaa.ElasticTransformation()  # Random Elastic Deformations
])

# Dataset
train_path = Path("Preprocessed/train/")
val_path = Path("Preprocessed/val/")

train_dataset = CardiacDataset(train_path, seq) # nur das train dataset wird augmented
val_dataset = CardiacDataset(val_path, None)

# Dataloader
batch_size = 8
num_workers = 4

train_loader = torch.utils.data.DataLoader(train_dataset, batch_size=batch_size, num_workers=num_workers,shuffle=True)
val_loader = torch.utils.data.DataLoader(val_dataset, batch_size=batch_size, num_workers=num_workers, shuffle=False)


# Lossfunction (Dic Loss)
class DiceLoss(torch.nn.Module):
    def __init__(self):
        super().__init__()

    def forward(self, pred, mask): # predicted segmentation, real segmentation
        pred = torch.flatten(pred)
        mask = torch.flatten(mask)

        counter = (pred * mask).sum()
        denum = pred.sum() + mask.sum() + 1e-8 #  1e-8, so that we never divide by 0
        dice = (2*counter) / denum
        return 1 - dice
    

# Segmentation Model
class BrainTumorSegmentation(pl.LightningModule):
    def __init__(self):
        super().__init__()

        self.model = UNet()

        self.optimizer = torch.optim.Adam(self.model.parameters(), lr= 1e-4)
        self.loss_fn = DiceLoss()

    def forward(self, data):
        return torch.sigmoid(self.model(data))
    
    def training_step(self, batch, batch_idx):
        mri, mask = batch              
        mask = mask.float() # real segmentation
        pred = self(mri) # predicted segmentation

        loss = self.loss_fn(pred, mask)

        self.log("Train Dice", loss)
        return loss
    
    def validation_step(self, batch, batch_idx):
        mri, mask = batch              
        mask = mask.float() # real segmentation
        pred = self(mri) # predicted segmentation

        loss = self.loss_fn(pred, mask)

        self.log("Val Dice", loss)
        return loss

    def configure_optimizers(self):
        return [self.optimizer]
    

# Training
if __name__ == '__main__':
    torch.manual_seed(0)
    model = BrainTumorSegmentation()

    torch.cuda.device(1) # <-- TODO: Does this assign a specific GPU?
    checkpoint_callback = ModelCheckpoint(monitor="Val Dice", save_top_k=10, mode="min")
    trainer = pl.Trainer(devices=1, accelerator="gpu", logger=TensorBoardLogger(save_dir="logs"), log_every_n_steps=1, callbacks = checkpoint_callback, max_epochs=75)
    trainer.fit(model, train_loader, val_loader)
