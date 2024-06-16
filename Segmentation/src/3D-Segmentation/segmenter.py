import torch


class Segmenter(pl.LightningModule):
    def __init__(self):
        super().__init__()
        self.model = UNet()
        self.optimizer = torch.optim.Adam(self.model.parameters(), lr=1e-4)
        self.loss_fn = torch.nn.CrossEntropyLoss()
    
    def forward(self, x):
        return self.model(x)
    
    def training_step(self, batch, batch_idx):
        # This is the CT scan. In torchio, the batch objects doesn't only contain the core volume data, but also
        # some metadata. Hence, we need to extract its data attribute.
        img = batch["CT"]["data"]
        # In order to use cross-entropy loss, we need to remove the channel dimension. TODO Why??
        mask = batch["Label"]["data"][:, 0]
        mask = mask.long()
        
        pred = self(img)
        loss = self.loss_fn(pred, mask)
        self.log("Train Loss", loss)
        return loss
    
    def validation_step(self, batch, batch_idx):
        # This is the CT scan. In torchio, the batch objects doesn't only contain the core volume data, but also
        # some metadata. Hence, we need to extract its data attribute.
        img = batch["CT"]["data"]
        # In order to use cross-entropy loss, we need to remove the channel dimension. TODO Why??
        mask = batch["Label"]["data"][:, 0]
        mask = mask.long()
        
        pred = self(img)
        loss = self.loss_fn(pred, mask)
        self.log("Val Loss", loss)
        return loss
    
    def configure_optimizers(self):
        return [self.optimizer]