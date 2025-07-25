import torch


class DoubleConv(torch.nn.Module):
    def __init__(self, in_channels: int, out_channels: int, kernel_size: int, activation_fn: torch.nn.Module, use_batch_norm: bool):
        super().__init__()

        # Ensure that the kernel size is odd.
        assert kernel_size % 2 == 1
        padding = kernel_size // 2
        if use_batch_norm:
            self.step = torch.nn.Sequential(torch.nn.Conv3d(in_channels, out_channels, kernel_size=kernel_size, padding=padding),
                torch.nn.BatchNorm3d(out_channels),
                activation_fn,
                torch.nn.Conv3d(out_channels, out_channels, kernel_size=kernel_size, padding=padding),
                torch.nn.BatchNorm3d(out_channels),
                activation_fn
            )
        else:
            self.step = torch.nn.Sequential(torch.nn.Conv3d(in_channels, out_channels, kernel_size=kernel_size, padding=padding),
                activation_fn,
                torch.nn.Conv3d(out_channels, out_channels, kernel_size=kernel_size, padding=padding),
                activation_fn
            )

    def forward(self, X):
        return self.step(X)


class UNet(torch.nn.Module):
    def __init__(self, in_channels: int, out_channels: int, odd_kernel_size: int, activation_fn: torch.nn.Module,
                 dropout_probability: float = 0, use_batch_norm: bool = False):
        super().__init__()

        self.layer1 = DoubleConv(in_channels=in_channels, out_channels=32, kernel_size=odd_kernel_size,
                                 activation_fn=activation_fn, use_batch_norm=use_batch_norm)
        self.layer2 = DoubleConv(in_channels=32, out_channels=64, kernel_size=odd_kernel_size,
                                 activation_fn=activation_fn, use_batch_norm=use_batch_norm)
        self.layer3 = DoubleConv(in_channels=64, out_channels=128, kernel_size=odd_kernel_size,
                                 activation_fn=activation_fn, use_batch_norm=use_batch_norm)
        self.layer4 = DoubleConv(in_channels=128, out_channels=256, kernel_size=odd_kernel_size,
                                 activation_fn=activation_fn, use_batch_norm=use_batch_norm)

        self.layer5 = DoubleConv(in_channels=256 + 128, out_channels=128, kernel_size=odd_kernel_size,
                                 activation_fn=activation_fn, use_batch_norm=use_batch_norm)
        self.layer6 = DoubleConv(in_channels=128 + 64, out_channels=64, kernel_size=odd_kernel_size,
                                 activation_fn=activation_fn, use_batch_norm=use_batch_norm)
        self.layer7 = DoubleConv(in_channels=64 + 32, out_channels=32, kernel_size=odd_kernel_size,
                                 activation_fn=activation_fn, use_batch_norm=use_batch_norm)
        self.layer8 = torch.nn.Conv3d(in_channels=32, out_channels=out_channels, kernel_size=1)

        self.maxpool = torch.nn.MaxPool3d(2)
        # Apply Softmax along the channel dimension
        self.softmax = torch.nn.Softmax(dim=1)
        # Use elementwise dropout
        self.dropout = torch.nn.Dropout(dropout_probability)

    def forward(self, x):
        x1 = self.layer1(x)
        x1m = self.maxpool(x1)
        x1m = self.dropout(x1m)

        x2 = self.layer2(x1m)
        x2m = self.maxpool(x2)
        x2m = self.dropout(x2m)

        x3 = self.layer3(x2m)
        x3m = self.maxpool(x3)
        x3m = self.dropout(x3m)

        x4 = self.layer4(x3m)
        x4 = self.dropout(x4)

        x5 = torch.nn.Upsample(scale_factor=2, mode="trilinear")(x4)
        x5 = torch.cat([x5, x3], dim=1)
        x5 = self.layer5(x5)
        x5 = self.dropout(x5)

        x6 = torch.nn.Upsample(scale_factor=2, mode="trilinear")(x5)
        x6 = torch.cat([x6, x2], dim=1)
        x6 = self.layer6(x6)
        x6 = self.dropout(x6)

        x7 = torch.nn.Upsample(scale_factor=2, mode="trilinear")(x6)
        x7 = torch.cat([x7, x1], dim=1)
        x7 = self.layer7(x7)
        x7 = self.dropout(x7)

        x8 = self.layer8(x7)
        x8 = self.dropout(x8)

        return x8
