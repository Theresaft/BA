import torch

class DiceLoss(torch.nn.Module):
    """ A scratch implementation of Dice loss. Forward computes the loss between the prediction and the
     true value, i.e., the mask. """
    def __init__(self):
        super().__init__()

    def forward(self, pred, mask): # predicted segmentation, real segmentation
        pred = torch.flatten(pred)
        mask = torch.flatten(mask)

        counter = (pred * mask).sum()
        denum = pred.sum() + mask.sum() + 1e-8 #  1e-8, so that we never divide by 0
        dice = (2*counter) / denum
        return 1 - dice