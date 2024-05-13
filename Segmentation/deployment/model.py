import torch

class DoubleConv(torch.nn.Module):
    def __init__(self, in_channels, out_channels):
        super().__init__()
        self.step = torch.nn.Sequential(
            torch.nn.Conv2d(in_channels, out_channels, kernel_size = 3, padding = 1),
            torch.nn.ReLU(),
            torch.nn.Conv2d(out_channels, out_channels, kernel_size = 3, padding = 1),
            torch.nn.ReLU()
        )


    def forward(self, X):
        return self.step(X)
    


class UNet(torch.nn.Module):
    def __init__(self):
        super().__init__()
        # Encoding Layers
        self.layer1 = DoubleConv(in_channels = 1, out_channels = 64)
        self.layer2 = DoubleConv(in_channels = 64, out_channels = 128)
        self.layer3 = DoubleConv(in_channels = 128, out_channels = 256)
        self.layer4 = DoubleConv(in_channels = 256, out_channels = 512)

        # Decoding Layers
        self.layer5 = DoubleConv(in_channels = 512+256, out_channels = 256) # verbunden mit layer3
        self.layer6 = DoubleConv(in_channels = 256+128, out_channels = 128) # verbunden mit layer2
        self.layer7 = DoubleConv(in_channels = 128+64, out_channels = 64) # verbunden mit layer1
        self.layer8 = torch.nn.Conv2d(in_channels = 64, out_channels = 1, kernel_size = 1)

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
        x5 = torch.nn.Upsample(scale_factor=2, mode="bilinear")(x4) # Upsample x4
        x5 = torch.cat([x5, x3], dim=1) # konkatinierte features: verbindung zwischen layer5 und layer3. Channel dim = 1
        x5 = self.layer5(x5)

        x6 = torch.nn.Upsample(scale_factor=2, mode="bilinear")(x5) 
        x6 = torch.cat([x6, x2], dim=1) 
        x6 = self.layer6(x6)

        x7 = torch.nn.Upsample(scale_factor=2, mode="bilinear")(x6) 
        x7 = torch.cat([x7, x1], dim=1) 
        x7 = self.layer7(x7)

        ret = self.layer8(x7)

        return ret
    
# Test model
model = UNet()
random_input = torch.randn(1,1,256,256) # (batch size, channel dimension, pixel width, pixel height)
output = model(random_input)
assert output.shape == torch.Size([1,1,256,256])
print(output)