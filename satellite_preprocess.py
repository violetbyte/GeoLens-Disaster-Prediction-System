from pathlib import Path
import argparse

import numpy as np
import rasterio
from rasterio.enums import Resampling


# ============================================================
# CONFIGURATION
# ============================================================

DEFAULT_SIZE = 256
LOW_PERCENTILE = 2
HIGH_PERCENTILE = 98


# ============================================================
# LOAD SATELLITE IMAGE
# ============================================================

def load_satellite(path):
    """
    Load a GeoTIFF satellite image.

    Returns:
        image   -> NumPy array [bands, height, width]
        profile -> Rasterio metadata
    """

    path = Path(path)

    if not path.exists():
        raise FileNotFoundError(
            f"Satellite file not found: {path}"
        )

    with rasterio.open(path) as src:

        image = src.read().astype(np.float32)

        profile = src.profile.copy()

    print(f"Loaded: {path}")
    print(f"Bands: {image.shape[0]}")
    print(
        f"Size: "
        f"{image.shape[2]} x "
        f"{image.shape[1]}"
    )

    return image, profile


# ============================================================
# RESIZE
# ============================================================

def resize_image(input_path, size=DEFAULT_SIZE):
    """
    Read and resize a satellite image.

    The number of bands is preserved.
    """

    input_path = Path(input_path)

    if not input_path.exists():
        raise FileNotFoundError(
            f"Input file not found: {input_path}"
        )

    with rasterio.open(input_path) as src:

        image = src.read(
            out_shape=(
                src.count,
                size,
                size
            ),
            resampling=Resampling.bilinear
        ).astype(np.float32)

        profile = src.profile.copy()

        profile.update(
            height=size,
            width=size,
            dtype="float32",
            count=src.count,
            compress="deflate"
        )

    return image, profile


# ============================================================
# INVALID VALUES
# ============================================================

def replace_invalid_values(image):
    """
    Replace NaN and infinite values with zero.
    """

    return np.nan_to_num(
        image,
        nan=0.0,
        posinf=0.0,
        neginf=0.0
    ).astype(np.float32)


# ============================================================
# PERCENTILE CLIPPING
# ============================================================

def percentile_clip(image):
    """
    Clip extreme values independently for every band.
    """

    output = np.zeros_like(
        image,
        dtype=np.float32
    )

    for band in range(image.shape[0]):

        current = image[band]

        valid = current[
            np.isfinite(current)
        ]

        if len(valid) == 0:
            continue

        lower = np.percentile(
            valid,
            LOW_PERCENTILE
        )

        upper = np.percentile(
            valid,
            HIGH_PERCENTILE
        )

        if upper <= lower:

            output[band] = current

            continue

        output[band] = np.clip(
            current,
            lower,
            upper
        )

    return output


# ============================================================
# NORMALIZE SINGLE IMAGE
# ============================================================

def normalize(image):
    """
    Normalize each band independently to [0, 1].

    This function is suitable for standalone
    image preprocessing.
    """

    output = np.zeros_like(
        image,
        dtype=np.float32
    )

    for band in range(image.shape[0]):

        current = image[band]

        min_value = np.min(current)
        max_value = np.max(current)

        if max_value == min_value:

            output[band] = 0.0

            continue

        output[band] = (
            current - min_value
        ) / (
            max_value - min_value
        )

    return output


# ============================================================
# NORMALIZE HISTORICAL + RECENT TOGETHER
# ============================================================

def normalize_pair(historical, recent):
    """
    Normalize historical and recent images using
    COMMON statistics for each band.

    This is important for temporal change detection.

    If historical and recent images were normalized
    independently, an actual change in intensity could
    partially disappear after normalization.
    """

    if historical.shape != recent.shape:

        raise ValueError(
            "Historical and recent images must have "
            "the same shape."
        )

    historical_output = np.zeros_like(
        historical,
        dtype=np.float32
    )

    recent_output = np.zeros_like(
        recent,
        dtype=np.float32
    )

    for band in range(
        historical.shape[0]
    ):

        historical_band = historical[band]
        recent_band = recent[band]

        combined = np.concatenate(
            [
                historical_band.ravel(),
                recent_band.ravel()
            ]
        )

        min_value = np.min(combined)
        max_value = np.max(combined)

        if max_value == min_value:

            historical_output[band] = 0.0
            recent_output[band] = 0.0

            continue

        historical_output[band] = (
            historical_band - min_value
        ) / (
            max_value - min_value
        )

        recent_output[band] = (
            recent_band - min_value
        ) / (
            max_value - min_value
        )

    return (
        historical_output,
        recent_output
    )


# ============================================================
# PREPROCESS SINGLE IMAGE
# ============================================================

def preprocess(
    input_path,
    output_path,
    size=DEFAULT_SIZE
):
    """
    Complete preprocessing pipeline for one image.
    """

    print("\n" + "=" * 60)
    print("SINGLE IMAGE PREPROCESSING")
    print("=" * 60)

    # 1. Resize
    image, profile = resize_image(
        input_path,
        size
    )

    print(
        f"Resized image shape: "
        f"{image.shape}"
    )

    # 2. Remove invalid values
    image = replace_invalid_values(
        image
    )

    # 3. Clip extreme values
    image = percentile_clip(
        image
    )

    # 4. Normalize
    image = normalize(
        image
    )

    # 5. Output path
    output_path = Path(
        output_path
    )

    output_path.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    # 6. Save
    with rasterio.open(
        output_path,
        "w",
        **profile
    ) as dst:

        dst.write(image)

    print("\nPreprocessing complete!")

    print(
        f"Output: {output_path}"
    )

    print(
        f"Shape: {image.shape}"
    )

    print(
        f"Range: "
        f"{image.min():.4f} -> "
        f"{image.max():.4f}"
    )


# ============================================================
# PREPROCESS IMAGE PAIR
# ============================================================

def preprocess_pair(
    historical_path,
    recent_path,
    historical_output,
    recent_output,
    size=DEFAULT_SIZE
):
    """
    Preprocess a historical + recent image pair.

    Both images are:
        1. Resized
        2. Cleaned
        3. Percentile clipped
        4. Normalized using COMMON statistics
        5. Saved separately
    """

    print("\n" + "=" * 60)
    print("TEMPORAL IMAGE PAIR PREPROCESSING")
    print("=" * 60)

    # --------------------------------------------------------
    # Load and resize historical
    # --------------------------------------------------------

    historical, historical_profile = resize_image(
        historical_path,
        size
    )

    # --------------------------------------------------------
    # Load and resize recent
    # --------------------------------------------------------

    recent, recent_profile = resize_image(
        recent_path,
        size
    )

    print(
        f"Historical shape: "
        f"{historical.shape}"
    )

    print(
        f"Recent shape: "
        f"{recent.shape}"
    )

    # --------------------------------------------------------
    # Validate shape
    # --------------------------------------------------------

    if historical.shape != recent.shape:

        raise ValueError(
            "Historical and recent images must have "
            "the same number of bands and dimensions."
        )

    # --------------------------------------------------------
    # Replace invalid values
    # --------------------------------------------------------

    historical = replace_invalid_values(
        historical
    )

    recent = replace_invalid_values(
        recent
    )

    # --------------------------------------------------------
    # Clip
    # --------------------------------------------------------

    historical = percentile_clip(
        historical
    )

    recent = percentile_clip(
        recent
    )

    # --------------------------------------------------------
    # COMMON NORMALIZATION
    # --------------------------------------------------------

    (
        historical,
        recent
    ) = normalize_pair(
        historical,
        recent
    )

    # --------------------------------------------------------
    # Prepare output paths
    # --------------------------------------------------------

    historical_output = Path(
        historical_output
    )

    recent_output = Path(
        recent_output
    )

    historical_output.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    recent_output.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    # --------------------------------------------------------
    # Update profiles
    # --------------------------------------------------------

    historical_profile.update(
        height=size,
        width=size,
        dtype="float32",
        count=historical.shape[0],
        compress="deflate"
    )

    recent_profile.update(
        height=size,
        width=size,
        dtype="float32",
        count=recent.shape[0],
        compress="deflate"
    )

    # --------------------------------------------------------
    # Save historical
    # --------------------------------------------------------

    with rasterio.open(
        historical_output,
        "w",
        **historical_profile
    ) as dst:

        dst.write(historical)

    # --------------------------------------------------------
    # Save recent
    # --------------------------------------------------------

    with rasterio.open(
        recent_output,
        "w",
        **recent_profile
    ) as dst:

        dst.write(recent)

    print("\nPair preprocessing complete!")

    print(
        f"Historical output: "
        f"{historical_output}"
    )

    print(
        f"Recent output: "
        f"{recent_output}"
    )

    print(
        f"Bands: "
        f"{historical.shape[0]}"
    )

    print(
        f"Size: "
        f"{size} x {size}"
    )


# ============================================================
# COMMAND LINE
# ============================================================

def main():

    parser = argparse.ArgumentParser(
        description=(
            "Preprocess satellite GeoTIFF imagery."
        )
    )

    parser.add_argument(
        "--input",
        required=True,
        help="Input GeoTIFF"
    )

    parser.add_argument(
        "--output",
        required=True,
        help="Output processed GeoTIFF"
    )

    parser.add_argument(
        "--size",
        type=int,
        default=DEFAULT_SIZE,
        help="Output image size"
    )

    args = parser.parse_args()

    preprocess(
        args.input,
        args.output,
        args.size
    )


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":
    main()