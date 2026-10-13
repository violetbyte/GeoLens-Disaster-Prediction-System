from pathlib import Path
import argparse

import numpy as np
import torch
import rasterio

from models.disaster_cnn import TemporalDisasterCNN
from preprocessing.satellite_preprocessing import (
    replace_invalid_values,
    percentile_clip,
    normalize_pair
)


# ============================================================
# PATHS
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parent

DEFAULT_MODEL = (
    PROJECT_ROOT /
    "models" /
    "best_disaster_cnn.pth"
)


# ============================================================
# DEVICE
# ============================================================

def get_device():

    if torch.cuda.is_available():

        device = torch.device("cuda")

        print(
            f"\nUsing GPU: "
            f"{torch.cuda.get_device_name(0)}"
        )

    else:

        device = torch.device("cpu")

        print("\nUsing CPU")

    return device


# ============================================================
# LOAD GEOTIFF
# ============================================================

def load_image(path):

    path = Path(path)

    if not path.exists():

        raise FileNotFoundError(
            f"\nSatellite image not found:\n{path}"
        )

    with rasterio.open(path) as src:

        image = src.read().astype(
            np.float32
        )

        height = src.height
        width = src.width
        bands = src.count

    print(
        f"\nLoaded: {path.name}"
    )

    print(
        f"Bands: {bands}"
    )

    print(
        f"Size: {width} x {height}"
    )

    return image


# ============================================================
# RESIZE IMAGE
# ============================================================

def resize_image(path, size=256):

    path = Path(path)

    with rasterio.open(path) as src:

        image = src.read(
            out_shape=(
                src.count,
                size,
                size
            ),
            resampling=rasterio.enums.Resampling.bilinear
        ).astype(np.float32)

    return image


# ============================================================
# PREPROCESS PAIR
# ============================================================

def preprocess_pair(
    historical_path,
    recent_path,
    size=256
):
    """
    Apply the same preprocessing pipeline used
    during dataset preparation.

    Both images are normalized using common
    statistics.
    """

    print(
        "\nPreprocessing satellite pair..."
    )

    # --------------------------------------------------------
    # Resize
    # --------------------------------------------------------

    historical = resize_image(
        historical_path,
        size
    )

    recent = resize_image(
        recent_path,
        size
    )

    # --------------------------------------------------------
    # Validate shape
    # --------------------------------------------------------

    if historical.shape != recent.shape:

        raise ValueError(
            "\nHistorical and recent images "
            "must have identical shapes.\n\n"
            f"Historical: {historical.shape}\n"
            f"Recent:     {recent.shape}"
        )

    # --------------------------------------------------------
    # Invalid values
    # --------------------------------------------------------

    historical = replace_invalid_values(
        historical
    )

    recent = replace_invalid_values(
        recent
    )

    # --------------------------------------------------------
    # Percentile clipping
    # --------------------------------------------------------

    historical = percentile_clip(
        historical
    )

    recent = percentile_clip(
        recent
    )

    # --------------------------------------------------------
    # Common normalization
    # --------------------------------------------------------

    (
        historical,
        recent
    ) = normalize_pair(
        historical,
        recent
    )

    # --------------------------------------------------------
    # Convert to tensors
    # --------------------------------------------------------

    historical = torch.tensor(
        historical,
        dtype=torch.float32
    )

    recent = torch.tensor(
        recent,
        dtype=torch.float32
    )

    # --------------------------------------------------------
    # Add batch dimension
    # --------------------------------------------------------

    historical = historical.unsqueeze(
        0
    )

    recent = recent.unsqueeze(
        0
    )

    return historical, recent


# ============================================================
# LOAD MODEL
# ============================================================

def load_model(
    model_path,
    device
):

    model_path = Path(
        model_path
    )

    if not model_path.exists():

        raise FileNotFoundError(
            f"\nModel not found:\n"
            f"{model_path}\n\n"
            "Train the model first using:\n"
            "python train.py"
        )

    print(
        "\nLoading trained model..."
    )

    checkpoint = torch.load(
        model_path,
        map_location=device
    )

    # --------------------------------------------------------
    # Read information saved by train.py
    # --------------------------------------------------------

    input_channels = checkpoint[
        "input_channels"
    ]

    class_names = checkpoint[
        "class_names"
    ]

    # --------------------------------------------------------
    # Create model
    # --------------------------------------------------------

    model = TemporalDisasterCNN(
        in_channels=input_channels,
        num_classes=len(class_names)
    )

    # --------------------------------------------------------
    # Load weights
    # --------------------------------------------------------

    model.load_state_dict(
        checkpoint[
            "model_state_dict"
        ]
    )

    model = model.to(
        device
    )

    model.eval()

    print(
        f"Model input channels: "
        f"{input_channels}"
    )

    print(
        f"Classes: "
        f"{class_names}"
    )

    print(
        f"Trained epoch: "
        f"{checkpoint.get('epoch', 'unknown')}"
    )

    print(
        f"Validation accuracy: "
        f"{checkpoint.get('validation_accuracy', 0):.2f}%"
    )

    return (
        model,
        class_names,
        input_channels
    )


# ============================================================
# CHANGE SCORE
# ============================================================

def calculate_change_score(
    historical,
    recent
):
    """
    Calculate a simple normalized temporal
    change score.

    This is a project-level indicator and
    should NOT be interpreted as physical
    disaster probability.
    """

    difference = torch.abs(
        recent -
        historical
    )

    change_score = (
        difference.mean().item()
    )

    # Convert roughly to percentage
    change_percentage = (
        change_score *
        100
    )

    return change_percentage


# ============================================================
# RISK LEVEL
# ============================================================

def calculate_risk(
    predicted_class,
    confidence,
    change_percentage
):

    # --------------------------------------------------------
    # Normal prediction
    # --------------------------------------------------------

    if predicted_class == "normal":

        if (
            confidence >= 0.80
            and change_percentage < 15
        ):

            return "LOW"

        elif (
            confidence >= 0.60
            and change_percentage < 30
        ):

            return "MEDIUM"

        else:

            return "MEDIUM"

    # --------------------------------------------------------
    # Disaster prediction
    # --------------------------------------------------------

    if (
        confidence >= 0.80
        and change_percentage >= 30
    ):

        return "HIGH"

    if (
        confidence >= 0.60
        or change_percentage >= 20
    ):

        return "MEDIUM"

    return "LOW"


# ============================================================
# PREDICTION
# ============================================================

def predict(
    model,
    class_names,
    historical,
    recent,
    device
):

    historical = historical.to(
        device
    )

    recent = recent.to(
        device
    )

    # --------------------------------------------------------
    # Inference
    # --------------------------------------------------------

    with torch.no_grad():

        outputs = model(
            historical,
            recent
        )

        probabilities = torch.softmax(
            outputs,
            dim=1
        )

        predicted_index = torch.argmax(
            probabilities,
            dim=1
        ).item()

    # --------------------------------------------------------
    # Predicted class
    # --------------------------------------------------------

    predicted_class = (
        class_names[
            predicted_index
        ]
    )

    confidence = (
        probabilities[
            0,
            predicted_index
        ].item()
    )

    # --------------------------------------------------------
    # Change score
    # --------------------------------------------------------

    change_percentage = (
        calculate_change_score(
            historical,
            recent
        )
    )

    # --------------------------------------------------------
    # Risk
    # --------------------------------------------------------

    risk_level = calculate_risk(
        predicted_class,
        confidence,
        change_percentage
    )

    return (
        predicted_class,
        confidence,
        probabilities,
        change_percentage,
        risk_level
    )


# ============================================================
# DISPLAY RESULTS
# ============================================================

def display_results(
    predicted_class,
    confidence,
    probabilities,
    class_names,
    change_percentage,
    risk_level
):

    print("\n")
    print("=" * 70)
    print("SATELLITE DISASTER PREDICTION")
    print("=" * 70)

    print(
        f"\nPredicted condition : "
        f"{predicted_class.upper()}"
    )

    print(
        f"Model confidence    : "
        f"{confidence * 100:.2f}%"
    )

    print(
        f"Temporal change     : "
        f"{change_percentage:.2f}%"
    )

    print(
        f"Risk level           : "
        f"{risk_level}"
    )

    print(
        "\nClass probabilities:"
    )

    print(
        "-" * 40
    )

    for index, class_name in enumerate(
        class_names
    ):

        probability = (
            probabilities[
                0,
                index
            ].item()
        )

        print(
            f"{class_name:<15}"
            f"{probability * 100:>8.2f}%"
        )

    print(
        "-" * 40
    )

    # --------------------------------------------------------
    # Warning
    # --------------------------------------------------------

    if risk_level == "HIGH":

        print(
            "\n!!! HIGH RISK DETECTED !!!"
        )

        print(
            "Further verification and "
            "human review are recommended."
        )

    elif risk_level == "MEDIUM":

        print(
            "\nMEDIUM RISK"
        )

        print(
            "Additional monitoring is recommended."
        )

    else:

        print(
            "\nLOW RISK"
        )

        print(
            "No strong disaster signal detected "
            "by the model."
        )

    print(
        "\nNOTE:"
    )

    print(
        "Risk level is a project-level heuristic "
        "based on model confidence and image change."
    )

    print(
        "It is not a certified emergency warning."
    )

    print(
        "=" * 70
    )


# ============================================================
# MAIN
# ============================================================

def main():

    parser = argparse.ArgumentParser(
        description=(
            "Temporal satellite disaster prediction"
        )
    )

    parser.add_argument(
        "--historical",
        required=True,
        help=(
            "Historical satellite GeoTIFF"
        )
    )

    parser.add_argument(
        "--recent",
        required=True,
        help=(
            "Recent satellite GeoTIFF"
        )
    )

    parser.add_argument(
        "--model",
        default=str(
            DEFAULT_MODEL
        ),
        help=(
            "Path to trained model"
        )
    )

    parser.add_argument(
        "--size",
        type=int,
        default=256,
        help=(
            "Input image size"
        )
    )

    args = parser.parse_args()

    # ========================================================
    # DEVICE
    # ========================================================

    device = get_device()

    # ========================================================
    # MODEL
    # ========================================================

    (
        model,
        class_names,
        input_channels
    ) = load_model(
        args.model,
        device
    )

    # ========================================================
    # IMAGES
    # ========================================================

    historical, recent = (
        preprocess_pair(
            args.historical,
            args.recent,
            args.size
        )
    )

    # ========================================================
    # CHANNEL CHECK
    # ========================================================

    actual_channels = (
        historical.shape[1]
    )

    if actual_channels != input_channels:

        raise ValueError(
            "\nChannel mismatch!\n\n"
            f"Model expects: "
            f"{input_channels} channels\n"
            f"Image contains: "
            f"{actual_channels} channels\n\n"
            "Use images with the same number "
            "of bands used during training."
        )

    # ========================================================
    # PREDICT
    # ========================================================

    (
        predicted_class,
        confidence,
        probabilities,
        change_percentage,
        risk_level
    ) = predict(
        model,
        class_names,
        historical,
        recent,
        device
    )

    # ========================================================
    # RESULTS
    # ========================================================

    display_results(
        predicted_class,
        confidence,
        probabilities,
        class_names,
        change_percentage,
        risk_level
    )


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":

    main()