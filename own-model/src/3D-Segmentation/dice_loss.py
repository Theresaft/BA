import torch

class DiceLoss(torch.nn.Module):
    """ A scratch implementation of Dice loss. Forward computes the loss between the prediction and the
     true value, i.e., the mask. """
    def __init__(self):
        super().__init__()

    def forward(self, pred, mask):
        pred_new = torch.flatten(pred)
        mask_new = torch.flatten(mask)
        return 1 - (2 * (pred_new * mask_new).sum() + 1) / (pred_new.sum() + mask_new.sum() + 1)