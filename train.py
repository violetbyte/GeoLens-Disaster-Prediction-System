from pathlib import Path
import random

import numpy as np
import torch
import torch.nn as nn

from torch.utils.data import DataLoader, random_split

from utils.dataset import TemporalSatelliteDataset
from models.disaster_cnn import TemporalDisasterCNN


# ============================================================
# CONFIGURATION
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parent

DATA_DIR = (
    PROJECT_ROOT /
    "data" /
    "processed"
)

MODEL_DIR = (
    PROJECT_ROOT /
    "models"
)

MODEL_PATH = (
    MODEL_DIR /
    "best_disaster_cnn.pth"
)


# Training parameters
BATCH_SIZE = 8
EPOCHS = 30
LEARNING_RATE = 0.001

# Validation percentage
VALIDATION_SPLIT = 0.20

# Number of workers
NUM_WORKERS = 0

# Reproducibility
SEED = 42

# Early stopping
PATIENCE = 7


# ============================================================
# REPRODUCIBILITY
# ============================================================

def set_seed(seed=SEED):

    random.seed(seed)

    np.random.seed(seed)

    torch.manual_seed(seed)

    if torch.cuda.is_available():

        torch.cuda.manual_seed_all(seed)


# ============================================================
# DEVICE
# ============================================================

def get_device():

    if torch.cuda.is_available():

        device = torch.device("cuda")

        print("\nGPU detected!")

        print(
            f"GPU: "
            f"{torch.cuda.get_device_name(0)}"
        )

    else:

        device = torch.device("cpu")

        print("\nCUDA GPU not available.")

        print("Training will use CPU.")

    return device


# ============================================================
# CREATE DATASET
# ============================================================

def create_dataset():

    print("\n" + "=" * 70)
    print("LOADING DATASET")
    print("=" * 70)

    dataset = TemporalSatelliteDataset(
        DATA_DIR
    )

    return dataset


# ============================================================
# TRAIN / VALIDATION SPLIT
# ============================================================

def split_dataset(dataset):

    total_size = len(dataset)

    validation_size = int(
        total_size *
        VALIDATION_SPLIT
    )

    training_size = (
        total_size -
        validation_size
    )

    if validation_size == 0:

        raise RuntimeError(
            "Dataset is too small for "
            "a validation split."
        )

    train_dataset, validation_dataset = (
        random_split(
            dataset,
            [
                training_size,
                validation_size
            ],
            generator=torch.Generator().manual_seed(
                SEED
            )
        )
    )

    print("\nDataset split:")

    print(
        f"Training samples: "
        f"{len(train_dataset)}"
    )

    print(
        f"Validation samples: "
        f"{len(validation_dataset)}"
    )

    return (
        train_dataset,
        validation_dataset
    )


# ============================================================
# CREATE DATALOADERS
# ============================================================

def create_dataloaders(
    train_dataset,
    validation_dataset
):

    train_loader = DataLoader(
        train_dataset,
        batch_size=BATCH_SIZE,
        shuffle=True,
        num_workers=NUM_WORKERS,
        pin_memory=torch.cuda.is_available()
    )

    validation_loader = DataLoader(
        validation_dataset,
        batch_size=BATCH_SIZE,
        shuffle=False,
        num_workers=NUM_WORKERS,
        pin_memory=torch.cuda.is_available()
    )

    return (
        train_loader,
        validation_loader
    )


# ============================================================
# DETECT NUMBER OF CHANNELS
# ============================================================

def detect_channels(dataset):

    historical, recent, _ = dataset[0]

    historical_channels = (
        historical.shape[0]
    )

    recent_channels = (
        recent.shape[0]
    )

    if historical_channels != recent_channels:

        raise RuntimeError(
            "Historical and recent images "
            "have different numbers of bands."
        )

    print("\nSatellite information:")

    print(
        f"Input channels/bands: "
        f"{historical_channels}"
    )

    print(
        f"Image size: "
        f"{historical.shape[1]} x "
        f"{historical.shape[2]}"
    )

    return historical_channels


# ============================================================
# CLASS WEIGHTS
# ============================================================

def calculate_class_weights(
    dataset
):
    """
    Calculate inverse-frequency class weights.

    This helps when some disaster classes have
    considerably fewer samples than others.
    """

    num_classes = len(
        dataset.class_names
    )

    class_counts = np.zeros(
        num_classes,
        dtype=np.float32
    )

    for _, _, label in dataset.samples:

        class_counts[label] += 1

    print("\nClass counts:")

    for index, count in enumerate(
        class_counts
    ):

        print(
            f"{dataset.class_names[index]:<12}: "
            f"{int(count)}"
        )

    # --------------------------------------------------------
    # Check for missing classes
    # --------------------------------------------------------

    if np.any(class_counts == 0):

        print(
            "\nWARNING:"
        )

        print(
            "One or more classes contain "
            "zero samples."
        )

        print(
            "The model cannot learn a class "
            "without training examples."
        )

    # --------------------------------------------------------
    # Calculate weights
    # --------------------------------------------------------

    weights = np.zeros_like(
        class_counts
    )

    total_samples = np.sum(
        class_counts
    )

    for i in range(num_classes):

        if class_counts[i] > 0:

            weights[i] = (
                total_samples /
                (
                    num_classes *
                    class_counts[i]
                )
            )

        else:

            weights[i] = 0.0

    return torch.tensor(
        weights,
        dtype=torch.float32
    )


# ============================================================
# TRAIN ONE EPOCH
# ============================================================

def train_one_epoch(
    model,
    loader,
    criterion,
    optimizer,
    device
):

    model.train()

    running_loss = 0.0

    correct = 0

    total = 0

    for (
        historical,
        recent,
        labels
    ) in loader:

        # ----------------------------------------------------
        # Move data to GPU/CPU
        # ----------------------------------------------------

        historical = historical.to(
            device,
            non_blocking=True
        )

        recent = recent.to(
            device,
            non_blocking=True
        )

        labels = labels.to(
            device,
            non_blocking=True
        )

        # ----------------------------------------------------
        # Clear gradients
        # ----------------------------------------------------

        optimizer.zero_grad()

        # ----------------------------------------------------
        # Forward pass
        # ----------------------------------------------------

        outputs = model(
            historical,
            recent
        )

        # ----------------------------------------------------
        # Calculate loss
        # ----------------------------------------------------

        loss = criterion(
            outputs,
            labels
        )

        # ----------------------------------------------------
        # Backpropagation
        # ----------------------------------------------------

        loss.backward()

        # ----------------------------------------------------
        # Update weights
        # ----------------------------------------------------

        optimizer.step()

        # ----------------------------------------------------
        # Statistics
        # ----------------------------------------------------

        batch_size = labels.size(0)

        running_loss += (
            loss.item() *
            batch_size
        )

        predictions = torch.argmax(
            outputs,
            dim=1
        )

        correct += (
            (predictions == labels)
            .sum()
            .item()
        )

        total += batch_size

    epoch_loss = (
        running_loss /
        total
    )

    epoch_accuracy = (
        correct /
        total
    ) * 100

    return (
        epoch_loss,
        epoch_accuracy
    )


# ============================================================
# VALIDATION
# ============================================================

def validate(
    model,
    loader,
    criterion,
    device
):

    model.eval()

    running_loss = 0.0

    correct = 0

    total = 0

    # --------------------------------------------------------
    # No gradients required
    # --------------------------------------------------------

    with torch.no_grad():

        for (
            historical,
            recent,
            labels
        ) in loader:

            historical = historical.to(
                device,
                non_blocking=True
            )

            recent = recent.to(
                device,
                non_blocking=True
            )

            labels = labels.to(
                device,
                non_blocking=True
            )

            # Forward
            outputs = model(
                historical,
                recent
            )

            # Loss
            loss = criterion(
                outputs,
                labels
            )

            batch_size = labels.size(0)

            running_loss += (
                loss.item() *
                batch_size
            )

            # Predictions
            predictions = torch.argmax(
                outputs,
                dim=1
            )

            correct += (
                (predictions == labels)
                .sum()
                .item()
            )

            total += batch_size

    validation_loss = (
        running_loss /
        total
    )

    validation_accuracy = (
        correct /
        total
    ) * 100

    return (
        validation_loss,
        validation_accuracy
    )


# ============================================================
# SAVE MODEL
# ============================================================

def save_model(
    model,
    optimizer,
    epoch,
    validation_loss,
    validation_accuracy,
    input_channels,
    class_names
):

    MODEL_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    checkpoint = {

        "epoch": epoch,

        "model_state_dict":
            model.state_dict(),

        "optimizer_state_dict":
            optimizer.state_dict(),

        "validation_loss":
            validation_loss,

        "validation_accuracy":
            validation_accuracy,

        "input_channels":
            input_channels,

        "class_names":
            class_names
    }

    torch.save(
        checkpoint,
        MODEL_PATH
    )

    print(
        f"\nBest model saved to:"
        f"\n{MODEL_PATH}"
    )


# ============================================================
# MAIN TRAINING FUNCTION
# ============================================================

def main():

    # --------------------------------------------------------
    # Seed
    # --------------------------------------------------------

    set_seed()

    # --------------------------------------------------------
    # Device
    # --------------------------------------------------------

    device = get_device()

    # --------------------------------------------------------
    # Dataset
    # --------------------------------------------------------

    dataset = create_dataset()

    # --------------------------------------------------------
    # Number of channels
    # --------------------------------------------------------

    input_channels = (
        detect_channels(
            dataset
        )
    )

    # --------------------------------------------------------
    # Number of classes
    # --------------------------------------------------------

    num_classes = len(
        dataset.class_names
    )

    print(
        f"Number of classes: "
        f"{num_classes}"
    )

    print(
        f"Classes: "
        f"{dataset.class_names}"
    )

    # --------------------------------------------------------
    # Split
    # --------------------------------------------------------

    (
        train_dataset,
        validation_dataset
    ) = split_dataset(
        dataset
    )

    # --------------------------------------------------------
    # DataLoaders
    # --------------------------------------------------------

    (
        train_loader,
        validation_loader
    ) = create_dataloaders(
        train_dataset,
        validation_dataset
    )

    # --------------------------------------------------------
    # Model
    # --------------------------------------------------------

    print("\n" + "=" * 70)
    print("CREATING TEMPORAL CNN")
    print("=" * 70)

    model = TemporalDisasterCNN(
        in_channels=input_channels,
        num_classes=num_classes
    )

    model = model.to(
        device
    )

    print(
        model
    )

    # --------------------------------------------------------
    # Class weights
    # --------------------------------------------------------

    class_weights = (
        calculate_class_weights(
            dataset
        )
    )

    class_weights = class_weights.to(
        device
    )

    # --------------------------------------------------------
    # Loss
    # --------------------------------------------------------

    criterion = nn.CrossEntropyLoss(
        weight=class_weights
    )

    # --------------------------------------------------------
    # Optimizer
    # --------------------------------------------------------

    optimizer = torch.optim.Adam(
        model.parameters(),
        lr=LEARNING_RATE
    )

    # --------------------------------------------------------
    # Training information
    # --------------------------------------------------------

    print("\n" + "=" * 70)
    print("TRAINING CONFIGURATION")
    print("=" * 70)

    print(
        f"Device:          {device}"
    )

    print(
        f"Batch size:      {BATCH_SIZE}"
    )

    print(
        f"Epochs:          {EPOCHS}"
    )

    print(
        f"Learning rate:   {LEARNING_RATE}"
    )

    print(
        f"Validation:      "
        f"{VALIDATION_SPLIT * 100:.0f}%"
    )

    print(
        f"Model path:      "
        f"{MODEL_PATH}"
    )

    print("=" * 70)

    # --------------------------------------------------------
    # Best model tracking
    # --------------------------------------------------------

    best_validation_loss = float(
        "inf"
    )

    best_validation_accuracy = 0.0

    epochs_without_improvement = 0

    # ========================================================
    # TRAINING LOOP
    # ========================================================

    for epoch in range(
        EPOCHS
    ):

        print(
            f"\nEpoch "
            f"{epoch + 1}/{EPOCHS}"
        )

        print(
            "-" * 60
        )

        # ----------------------------------------------------
        # Training
        # ----------------------------------------------------

        train_loss, train_accuracy = (
            train_one_epoch(
                model,
                train_loader,
                criterion,
                optimizer,
                device
            )
        )

        # ----------------------------------------------------
        # Validation
        # ----------------------------------------------------

        validation_loss, validation_accuracy = (
            validate(
                model,
                validation_loader,
                criterion,
                device
            )
        )

        # ----------------------------------------------------
        # Display
        # ----------------------------------------------------

        print(
            f"Train Loss: "
            f"{train_loss:.4f}"
        )

        print(
            f"Train Accuracy: "
            f"{train_accuracy:.2f}%"
        )

        print(
            f"Validation Loss: "
            f"{validation_loss:.4f}"
        )

        print(
            f"Validation Accuracy: "
            f"{validation_accuracy:.2f}%"
        )

        # ====================================================
        # BEST MODEL
        # ====================================================

        if validation_loss < best_validation_loss:

            best_validation_loss = (
                validation_loss
            )

            best_validation_accuracy = (
                validation_accuracy
            )

            epochs_without_improvement = 0

            save_model(
                model,
                optimizer,
                epoch + 1,
                validation_loss,
                validation_accuracy,
                input_channels,
                dataset.class_names
            )

        else:

            epochs_without_improvement += 1

            print(
                f"No improvement: "
                f"{epochs_without_improvement}/"
                f"{PATIENCE}"
            )

        # ====================================================
        # EARLY STOPPING
        # ====================================================

        if (
            epochs_without_improvement
            >= PATIENCE
        ):

            print(
                "\nEarly stopping triggered."
            )

            break

    # ========================================================
    # FINAL RESULT
    # ========================================================

    print("\n" + "=" * 70)
    print("TRAINING COMPLETE")
    print("=" * 70)

    print(
        f"Best validation loss: "
        f"{best_validation_loss:.4f}"
    )

    print(
        f"Best validation accuracy: "
        f"{best_validation_accuracy:.2f}%"
    )

    print(
        f"\nModel saved at:"
        f"\n{MODEL_PATH}"
    )

    print("=" * 70)


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":

    main()