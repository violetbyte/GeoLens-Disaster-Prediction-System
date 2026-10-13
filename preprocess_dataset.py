from pathlib import Path

from satellite_preprocessing import preprocess_pair


# ============================================================
# PROJECT PATHS
# ============================================================

# Satellite/
PROJECT_ROOT = Path(
    __file__
).resolve().parents[1]

RAW_DIR = PROJECT_ROOT / "data" / "raw"

PROCESSED_DIR = (
    PROJECT_ROOT /
    "data" /
    "processed"
)


# ============================================================
# DISASTER CLASSES
# ============================================================

DISASTERS = [
    "normal",
    "flood",
    "wildfire",
    "cyclone",
    "landslide"
]


# ============================================================
# PROCESS DATASET
# ============================================================

def main():

    total = 0
    skipped = 0
    failed = 0

    print("=" * 70)
    print("TEMPORAL SATELLITE DATASET PREPROCESSING")
    print("=" * 70)

    print(
        f"\nRaw directory: "
        f"{RAW_DIR}"
    )

    print(
        f"Processed directory: "
        f"{PROCESSED_DIR}"
    )

    # ========================================================
    # LOOP THROUGH CLASSES
    # ========================================================

    for disaster in DISASTERS:

        disaster_raw = (
            RAW_DIR / disaster
        )

        disaster_processed = (
            PROCESSED_DIR / disaster
        )

        historical_raw = (
            disaster_raw / "historical"
        )

        recent_raw = (
            disaster_raw / "recent"
        )

        historical_processed = (
            disaster_processed / "historical"
        )

        recent_processed = (
            disaster_processed / "recent"
        )

        # ----------------------------------------------------
        # Create output folders
        # ----------------------------------------------------

        historical_processed.mkdir(
            parents=True,
            exist_ok=True
        )

        recent_processed.mkdir(
            parents=True,
            exist_ok=True
        )

        print("\n" + "#" * 70)
        print(
            f"CLASS: {disaster.upper()}"
        )
        print("#" * 70)

        # ----------------------------------------------------
        # Check folders
        # ----------------------------------------------------

        if not historical_raw.exists():

            print(
                f"Historical folder missing: "
                f"{historical_raw}"
            )

            continue

        if not recent_raw.exists():

            print(
                f"Recent folder missing: "
                f"{recent_raw}"
            )

            continue

        # ----------------------------------------------------
        # Find historical files
        # ----------------------------------------------------

        historical_files = sorted(
            list(
                historical_raw.glob("*.tif")
            )
            +
            list(
                historical_raw.glob("*.tiff")
            )
        )

        print(
            f"Historical images: "
            f"{len(historical_files)}"
        )

        # ----------------------------------------------------
        # Process each historical image
        # ----------------------------------------------------

        for historical_file in historical_files:

            filename = historical_file.name

            recent_file = (
                recent_raw /
                filename
            )

            # ------------------------------------------------
            # Check corresponding recent image
            # ------------------------------------------------

            if not recent_file.exists():

                print(
                    "\nWARNING:"
                )

                print(
                    f"Recent image missing "
                    f"for: {filename}"
                )

                skipped += 1

                continue

            # ------------------------------------------------
            # Output filenames
            # ------------------------------------------------

            historical_output = (
                historical_processed /
                f"{historical_file.stem}_processed.tif"
            )

            recent_output = (
                recent_processed /
                f"{recent_file.stem}_processed.tif"
            )

            print("\n" + "-" * 60)

            print(
                f"Historical: "
                f"{historical_file.name}"
            )

            print(
                f"Recent:     "
                f"{recent_file.name}"
            )

            try:

                preprocess_pair(
                    historical_file,
                    recent_file,
                    historical_output,
                    recent_output
                )

                total += 1

            except Exception as e:

                failed += 1

                print(
                    "\nERROR:"
                )

                print(
                    f"Could not process "
                    f"{filename}"
                )

                print(
                    f"Reason: {e}"
                )

    # ========================================================
    # SUMMARY
    # ========================================================

    print("\n" + "=" * 70)
    print("DATASET PREPROCESSING COMPLETE")
    print("=" * 70)

    print(
        f"Successfully processed pairs: "
        f"{total}"
    )

    print(
        f"Skipped pairs: "
        f"{skipped}"
    )

    print(
        f"Failed pairs: "
        f"{failed}"
    )

    print("=" * 70)


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":
    main()