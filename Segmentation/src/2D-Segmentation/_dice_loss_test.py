import torch
from dice_loss import DiceLoss


y_hat = torch.tensor([
        [
            # 3 channels
            [[1., 1],
            [0, 0]],
            [[0, 0],
             [0, 1]],
            [[0, 0],
             [1, 0]],
        ],
        [
            # 3 channels
            [[0, 1],
            [0, 1]],
            [[1, 0],
             [1, 0]],
            [[0, 0],
             [0, 0]],
        ],
])


y = torch.tensor([
        [
            # 3 channels
            [[1., 1.],
            [0, 0]],
            [[0, 0],
             [1, 0]],
            [[0, 0],
             [0, 1]],
        ],
        [
            # 3 channels
            [[0, 1],
            [0, 1]],
            [[1, 0],
             [1, 0]],
            [[0, 0],
             [0, 0]],
        ],
])



def main():
    torch.set_printoptions(precision=2)
    print(y_hat)
    print((torch.softmax(y_hat, dim=1) * 100).type(torch.int16))
    print(torch.softmax(y_hat, dim=1).sum(dim=1))
    print(DiceLoss()(y_hat, y).item())

if __name__ == "__main__":
    main()
