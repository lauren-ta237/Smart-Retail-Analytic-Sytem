# Importing modules from the local data folder
from .downloader import download_dataset
from .extract import extract_archive
from .process import process_images
from .convert import convert_coco_to_yolo
from .store import save_metadata
import os

# Base directory for data storage
BASE_DIR = "data"

def run(name, url):
    """
    Executes the full data processing pipeline for a given dataset.
    
    Steps:
    1. Download dataset
    2. Extract archive
    3. Process images
    4. Convert annotations to YOLO format
    5. Save metadata
    """
    # Define paths for raw (downloaded) and processed outputs
    raw_dir = os.path.join(BASE_DIR, "raw", name)
    processed_dir = os.path.join(BASE_DIR, "processed", name)

    # Step 1: Download the dataset zip file
    filepath = download_dataset(name, url, raw_dir)
    
    # Step 2: Extract the downloaded zip file
    extract_archive(filepath, raw_dir)
    
    # Step 3: Process images (e.g., resize, normalize) from raw_dir to processed_dir
    process_images(raw_dir, processed_dir)

    # Step 4: Convert COCO annotations to YOLO format mapping class ID 1 to 0
    convert_coco_to_yolo(raw_dir, processed_dir, {1: 0})

    # Step 5: Generate and save metadata about the run
    save_metadata(name, raw_dir, processed_dir, f"{name}_meta.json")


if __name__ == "__main__":
    run("test", "https://storage.googleapis.com/download.tensorflow.org/example_images/flower_photos.tgz")