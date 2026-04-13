import os
import json

def save_metadata(name, raw_dir, processed_dir, output_file):
    """
    Scans the raw and processed directories to count files and saves the statistics to a JSON file.

    Args:
        name (str): The name of the dataset/batch.
        raw_dir (str): Path to the directory containing raw images.
        processed_dir (str): Path to the directory containing processed images.
        output_file (str): The file path where the metadata JSON will be saved.
    """
    metadata = {
        "name": name,
        # recursively count all files in the raw directory
        "raw_files": sum(len(f) for _, _, f in os.walk(raw_dir)),
        # recursively count all files in the processed directory
        "processed_files": sum(len(f) for _, _, f in os.walk(processed_dir))
    }

    # Save the metadata dictionary to a file with indentation for readability
    with open(output_file, "w") as f:
        json.dump(metadata, f, indent=4)