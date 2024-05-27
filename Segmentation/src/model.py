import torch
import math
import numpy as np


def print_big_np_array(array):
    np.set_printoptions(threshold=np.inf)
    print(array)
    np.set_printoptions(threshold=1000)

class DoubleConv(torch.nn.Module):
    def __init__(self, in_channels: int, out_channels: int, kernel_size: int, activation_fn: torch.nn.Module):
        super().__init__()
        padding = self.__get_padding_from_kernel_size(kernel_size)
        self.step = torch.nn.Sequential(
            torch.nn.Conv2d(in_channels, out_channels, kernel_size=kernel_size, padding=padding),
            activation_fn,
            torch.nn.Conv2d(out_channels, out_channels, kernel_size=kernel_size, padding=padding),
            activation_fn
        )

    def __get_padding_from_kernel_size(self, kernel_size: int) -> int:
        # Ensure that the kernel size is odd.
        assert kernel_size % 2 == 1
        return kernel_size // 2

    def forward(self, X):
        return self.step(X)


class UNet(torch.nn.Module):
    def __init__(self, in_channels: int, out_channels: int, odd_kernel_size: int, activation_fn: torch.nn.Module):
        """
        Initializes a UNet with the given number of in_channels, out_channels, kernel_size, and activation function.
        The model is supposed to be used for 2D images.
        :param in_channels: The number of input channels
        :param out_channels: The number of output channels
        :param odd_kernel_size: The kernel size, which has to be odd!
        :param activation_fn: The activation function to use in the double-convolutions.
        """
        super().__init__()
        # Encoding Layers
        self.layer1 = DoubleConv(in_channels=in_channels, out_channels=64, kernel_size=odd_kernel_size,
                                 activation_fn=activation_fn)
        self.layer2 = DoubleConv(in_channels=64, out_channels=128, kernel_size=odd_kernel_size,
                                 activation_fn=activation_fn)
        self.layer3 = DoubleConv(in_channels=128, out_channels=256, kernel_size=odd_kernel_size,
                                 activation_fn=activation_fn)
        self.layer4 = DoubleConv(in_channels=256, out_channels=512, kernel_size=odd_kernel_size,
                                 activation_fn=activation_fn)

        # Decoding Layers
        self.layer5 = DoubleConv(in_channels=512 + 256, out_channels=256, kernel_size=odd_kernel_size,
                                 activation_fn=activation_fn)
        self.layer6 = DoubleConv(in_channels=256 + 128, out_channels=128, kernel_size=odd_kernel_size,
                                 activation_fn=activation_fn)
        self.layer7 = DoubleConv(in_channels=128 + 64, out_channels=64, kernel_size=odd_kernel_size,
                                 activation_fn=activation_fn)
        self.layer8 = torch.nn.Conv2d(in_channels=64, out_channels=out_channels, kernel_size=1)

        # Pooling
        self.maxpool = torch.nn.MaxPool2d(2)

    def forward(self, x):
        # Encoding Layers
        x1 = self.layer1(x)
        x1m = self.maxpool(x1)

        x2 = self.layer2(x1m)
        x2m = self.maxpool(x2)

        x3 = self.layer3(x2m)
        x3m = self.maxpool(x3)

        x4 = self.layer4(x3m)

        # Decoding Layers
        x5 = torch.nn.Upsample(scale_factor=2, mode="bilinear")(x4)  # Upsample x4
        x5 = torch.cat([x5, x3], dim=1)
        x5 = self.layer5(x5)

        x6 = torch.nn.Upsample(scale_factor=2, mode="bilinear")(x5)
        x6 = torch.cat([x6, x2], dim=1)
        x6 = self.layer6(x6)

        x7 = torch.nn.Upsample(scale_factor=2, mode="bilinear")(x6)
        x7 = torch.cat([x7, x1], dim=1)
        x7 = self.layer7(x7)

        ret = self.layer8(x7)

        # with torch.no_grad():
        #    print("\n\n", ret.squeeze(0).mean(dim=(1, 2)))

        return ret


def main():
    # Test model
    model = UNet(1, 1, 11, torch.nn.ReLU())
    print(model)
    random_input = torch.randn(1, 1, 256, 256)  # (batch size, channel dimension, pixel width, pixel height)
    output = model(random_input)
    assert output.shape == torch.Size([1, 1, 256, 256])
    print(output)


if __name__ == "__main__":
    main()
