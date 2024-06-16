from brain_tumor_segmentation import BrainTumorSegmentation
import pytorch_lightning as pl
from dataset import TumorDataset
from argparse import ArgumentParser, Namespace
from pathlib import Path
import torch
import numpy as np
from tqdm.notebook import tqdm


def get_cmd_args() -> Namespace:
    parser = ArgumentParser()
    parser.add_argument("--val-path", dest="val_path", default="Preprocessed/val",
                        help="The directory where the validation data is located.")
    parser.add_argument("--checkpoint", dest="checkpoint", help="Path to the checkpoint to load.")
    args = parser.parse_args()

    return args


def main():
    cmd_args: Namespace = get_cmd_args()
    val_path = Path(cmd_args.val_path)
    checkpoint = cmd_args.checkpoint

    model: BrainTumorSegmentation = BrainTumorSegmentation.load_from_checkpoint(checkpoint,
    in_channels=4, out_channels=4, odd_kernel_size=3, activation_fn=torch.nn.ReLU())
    device = "cuda:0"
    model.eval()
    model.to(device)

    # Load validation dataset
    val_dataset = TumorDataset(val_path, None)
    preds = []
    labels = []

    val_loader = torch.utils.data.DataLoader(val_dataset, batch_size=8, num_workers=4, shuffle=False,
                                             persistent_workers=True, pin_memory=True, prefetch_factor=2)

    with torch.no_grad():
        for index, (slice, label) in enumerate(val_loader):
            slice = torch.tensor(slice).to(device)
            pred = model(slice)
            preds.append(pred.cpu())
            labels.append(torch.tensor(label))
            if index % 10 == 0:
                # res = 1 - model.loss_fn(torch.from_numpy(np.array(preds)), torch.from_numpy(np.array(labels))).item()
                print(f"------------- Iteration {index} / {len(val_dataset)}")

    preds = torch.cat(preds, 0)
    labels = torch.cat(labels, 0)

    print("Preds shape:", preds.shape, ", labels shape:", labels.shape)

    print("\n\nFinal Loss:", (model.loss_fn(preds, labels)).item())


if __name__ == "__main__":
    main()
