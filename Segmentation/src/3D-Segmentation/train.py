from pathlib import Path

import torchio as tio
import torch
import pytorch_lightning as pl
from pytorch_lightning.callbacks import ModelCheckpoint
from pytorch_lightning.loggers import TensorBoardLogger

from model import UNet
from segmenter import Segmenter

# TODO Change this function appropriately
def change_img_to_label_path(path):
    """ Returns all directories in a path. """
    parts = list(path.parts)
    # Replace path
    parts[parts.index("imagesTr")] = "labelsTr"
    return Path(*parts)


def main():
    # ----------- Preprocessing

    num_train_elements = 400

    path = Path("Task03_Liver_rs/imagesTr/")
    subject_paths = list(path.glob("liver_*"))
    subjects = []

    for subject_path in subject_paths:
        label_path = change_img_to_label_path(subject_path)
        subject = tio.Subject({"CT": tio.ScalarImage(subject_path), 
                            "Label": tio.LabelMap(label_path)})
        subjects.append(subject)

    for subject in subjects:
        assert subject["CT"].orientation == ("R", "A", "S")

    process = tio.Compose([
        tio.CropOrPad((256, 256, 200)),
        tio.RescaleIntensity((-1, 1))
    ])

    # The augmentation creates new imaages with scales between 0.9 and 1.1 as well as rotating by between -10 degrees and 10
    # degrees.
    augmentation = tio.RandomAffine(scales=(0.9, 1.1), degrees=(-10, 10))

    # The validatoin only gets the preprocessed data, whereas we create new images for the test data in the form of
    # augmented data with the above transformations.
    val_transform = process
    train_transform = tio.Compose([process, augmentation])

    # This is the train/test split:
    print(f"Training: {num_train_elements / len(subject_paths):.4f}, val: {1 - num_train_elements / len(subject_paths):.4f}")


    train_dataset = tio.SubjectsDataset(subjects[:num_train_elements], transform=train_transform)
    val_dataset = tio.SubjectsDataset(subjects[num_train_elements:], transform=val_transform)

    # The sampler decides with what probability each label should occur in the training. This allows us to oversample
    # the tumors by assigning the tumor label a higher probability. Specifically, background (label 0) has probability
    # 0.2, liver (label 1) has probability 0.3, and tumor (label 2) has probability 0.5.
    sampler = tio.data.LabelSampler(patch_size=96, label_name="Label", label_probabilities={0:0.2, 1:0.3, 2:0.5})

    # This is the queue that generates the actual patches from the images. The values max_length and num_workers
    # can be very memory-consuming and therefore have to be adapted to the specific hardware you're running this code
    # on.
    train_patches_queue = tio.Queue(
        train_dataset,
        max_length=40,
        samples_per_volume=5,
        sampler=sampler,
        num_workers=4
    )

    val_patches_queue = tio.Queue(
        val_dataset,
        max_length=40,
        samples_per_volume=5,
        sampler=sampler,
        num_workers=4
    )



    # ----------- Data loading and training
    train_loader = torch.utils.data.DataLoader(train_patches_queue, batch_size=2, num_workers=0)
    val_loader = torch.utils.data.DataLoader(val_patches_queue, batch_size=2, num_workers=0)

    model = Segmenter()
    checkpoint_callback = ModelCheckpoint(
        monitor="Val Loss",
        save_top_k=10,
        mode="min"
    )

    trainer = pl.Trainer(devices=[0], accelerator="cuda", logger=TensorBoardLogger(save_dir="./logs"), log_every_n_steps=1, 
                        callbacks=checkpoint_callback, max_epochs=30)
    trainer.fit(model, train_loader, val_loader)

if __name__ == "__main__":
    main()