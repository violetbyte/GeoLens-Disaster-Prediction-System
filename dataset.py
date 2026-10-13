from pathlib import Path

import torch
import rasterio

from torch.utils.data import Dataset


# ============================================================
# TEMPORAL SATELLITE DATASET
# ============================================================

class TemporalSatelliteDataset(Dataset):

    def __init__(
        self,
        root_dir,
        disasters=None
    ):

        self.root_dir = Path(
            root_dir
        )

        # ====================================================
        # CLASS DEFINITIONS
        # ====================================================

        self.class_names = [
            "normal",
            "flood",
            "wildfire",
            "cyclone",
            "landslide"
        ]

        self.class_to_index = {
            name: index
            for index, name
            in enumerate(
                self.class_names
            )
        }

        # ====================================================
        # SELECT CLASSES
        # ====================================================

        if disasters is None:

            disasters = self.class_names

        # ====================================================
        # STORAGE
        # ====================================================

        self.samples = []

        # ====================================================
        # FIND DATA
        # ====================================================

        for disaster in disasters:

            if disaster not in self.class_to_index:

                print(
                    f"WARNING: Unknown class "
                    f"{disaster}"
                )

                continue

            disaster_dir = (
                self.root_dir /
                disaster
            )

            historical_dir = (
                disaster_dir /
                "historical"
            )

            recent_dir = (
                disaster_dir /
                "recent"
            )

            # ------------------------------------------------
            # Check directories
            # ------------------------------------------------

            if not historical_dir.exists():

                print(
                    f"WARNING: Historical folder "
                    f"missing: {historical_dir}"
                )

                continue

            if not recent_dir.exists():

                print(
                    f"WARNING: Recent folder "
                    f"missing: {recent_dir}"
                )

                continue

            # ------------------------------------------------
            # Find historical files
            # ------------------------------------------------

            historical_files = sorted(
                list(
                    historical_dir.glob(
                        "*_processed.tif"
                    )
                )
                +
                list(
                    historical_dir.glob(
                        "*_processed.tiff"
                    )
                )
            )

            # ------------------------------------------------
            # Match historical + recent
            # ------------------------------------------------

            for historical_file in historical_files:

                filename = (
                    historical_file.name
                )

                recent_file = (
                    recent_dir /
                    filename
                )

                if not recent_file.exists():

                    print(
                        "WARNING: Missing recent "
                        f"image for {filename}"
                    )

                    continue

                label = (
                    self.class_to_index[
                        disaster
                    ]
                )

                self.samples.append(
                    (
                        historical_file,
                        recent_file,
                        label
                    )
                )

        # ====================================================
        # DATASET SUMMARY
        # ====================================================

        print("\n" + "=" * 60)
        print("TEMPORAL DATASET")
        print("=" * 60)

        print(
            f"Root directory: "
            f"{self.root_dir}"
        )

        print(
            f"Total paired samples: "
            f"{len(self.samples)}"
        )

        print(
            f"Classes: "
            f"{self.class_names}"
        )

        # ====================================================
        # CLASS COUNTS
        # ====================================================

        class_counts = {
            class_name: 0
            for class_name
            in self.class_names
        }

        for _, _, label in self.samples:

            class_name = (
                self.class_names[label]
            )

            class_counts[
                class_name
            ] += 1

        print("\nClass distribution:")

        for class_name, count in class_counts.items():

            print(
                f"  {class_name:<12} "
                f"{count}"
            )

        print("=" * 60)

        # ====================================================
        # EMPTY DATASET CHECK
        # ====================================================

        if len(self.samples) == 0:

            raise RuntimeError(
                "\nNo valid historical/recent "
                "image pairs were found.\n\n"
                "Check that your dataset follows:\n"
                "class/historical/*.tif\n"
                "class/recent/*.tif\n\n"
                "and that corresponding filenames "
                "are identical."
            )

    # ========================================================
    # LENGTH
    # ========================================================

    def __len__(self):

        return len(
            self.samples
        )

    # ========================================================
    # LOAD IMAGE
    # ========================================================

    def load_image(self, path):
        """
        Load processed GeoTIFF.

        Returns:
            Tensor [channels, height, width]
        """

        path = Path(path)

        if not path.exists():

            raise FileNotFoundError(
                f"Image not found: {path}"
            )

        with rasterio.open(path) as src:

            image = src.read()

        image = torch.tensor(
            image,
            dtype=torch.float32
        )

        # ====================================================
        # VALIDATE VALUES
        # ====================================================

        if not torch.isfinite(
            image
        ).all():

            raise ValueError(
                f"Invalid NaN/Inf values "
                f"found in {path}"
            )

        return image

    # ========================================================
    # GET ITEM
    # ========================================================

    def __getitem__(self, index):

        (
            historical_path,
            recent_path,
            label
        ) = self.samples[index]

        # ----------------------------------------------------
        # Load historical
        # ----------------------------------------------------

        historical = self.load_image(
            historical_path
        )

        # ----------------------------------------------------
        # Load recent
        # ----------------------------------------------------

        recent = self.load_image(
            recent_path
        )

        # ====================================================
        # SHAPE VALIDATION
        # ====================================================

        if historical.shape != recent.shape:

            raise ValueError(
                "\nHistorical and recent "
                "images have different shapes.\n"
                f"Historical: "
                f"{historical.shape}\n"
                f"Recent: "
                f"{recent.shape}\n"
                f"Historical file: "
                f"{historical_path}\n"
                f"Recent file: "
                f"{recent_path}"
            )

        # ====================================================
        # LABEL
        # ====================================================

        label = torch.tensor(
            label,
            dtype=torch.long
        )

        return (
            historical,
            recent,
            label
        )


# ============================================================
# TEST DATASET
# ============================================================

if __name__ == "__main__":

    project_root = Path(
        __file__
    ).resolve().parents[1]

    processed_dir = (
        project_root /
        "data" /
        "processed"
    )

    print(
        "\nTesting dataset..."
    )

    dataset = TemporalSatelliteDataset(
        processed_dir
    )

    print(
        f"\nDataset size: "
        f"{len(dataset)}"
    )

    # --------------------------------------------------------
    # Test first sample
    # --------------------------------------------------------

    historical, recent, label = (
        dataset[0]
    )

    print(
        f"Historical shape: "
        f"{historical.shape}"
    )

    print(
        f"Recent shape: "
        f"{recent.shape}"
    )

    print(
        f"Label: "
        f"{label.item()}"
    )

    print(
        f"Class: "
        f"{dataset.class_names[label.item()]}"
    )