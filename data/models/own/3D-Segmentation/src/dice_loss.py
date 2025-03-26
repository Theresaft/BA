import torch
import torch.nn.functional as F
import typing

class DiceLoss(torch.nn.Module):
    """ A scratch implementation of Dice loss. Forward computes the loss between the prediction and the
     true value, i.e., the mask. """
    def __init__(self, channel_weights = None):
        """The weights applied in the dice loss function to the channels. If channel_weights != None, then
        the channels are considered separately and are weighted accordingly with a constant factor."""
        super().__init__()

        # Normalize the channel weights
        self.channel_weights = None if channel_weights is None else channel_weights / channel_weights.sum()
        # The current losses by channel. Gets overwritten during every call of forward, given self.channel_weights is defined.
        self.current_loss = None

    def forward(self, pred, target):
        """
        :param pred: The model's prediction with logits, i.e., before Softmax (which is applied in this function).
                        The shape should be (batch, channel, height, width, depth).
        :param mask: The ground truth label as integer encoding, i.e., before one-hot encoding (which is done here).
                        The shape should be (batch, height, width, depth)."""
        # Intersections and unions have shape (batch, channel)
        pred_softmax = F.softmax(pred, dim=1)

        # num_classes=4 is necessary if the mask contains 3 or fewer classes
        target_one_hot = F.one_hot(target, num_classes=4).float()
        # If a batch dimension is missing, unsqueeze the tensor.
        if target_one_hot.dim() == 4:
            target_one_hot = target_one_hot.unsqueeze(dim=0)

        target_one_hot = torch.transpose(target_one_hot, 1, 4)
        target_one_hot = torch.transpose(target_one_hot, 2, 4)
        target_one_hot = torch.transpose(target_one_hot, 3, 4)

        intersections = (pred_softmax * target_one_hot).sum(dim=(2, 3, 4))
        unions = (pred_softmax + target_one_hot).sum(dim=(2, 3, 4))

        # Per channel, get the mean dice value
        dice_per_channel = ((2 * intersections + 1) / (unions + 1)).mean(dim=0)

        # Weigh the channels differently if they are not None. Otherwise, weight them all equally
        if self.channel_weights is not None:
            # Get the sum because the weights are normalized
            dice = (dice_per_channel * self.channel_weights).sum()
            self.current_loss = 1 - dice_per_channel
        else:
            dice = dice_per_channel.mean()

        return 1 - dice