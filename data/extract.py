import zipfile
import tarfile

def extract_archive(filepath, extract_to):
    try:
        if zipfile.is_zipfile(filepath):
            with zipfile.ZipFile(filepath, 'r') as zip_ref:
                zip_ref.extractall(extract_to)

        elif tarfile.is_tarfile(filepath):
            with tarfile.open(filepath, 'r') as tar_ref:
                tar_ref.extractall(extract_to)
    except PermissionError:
        print(f"Notice: Skipped full extraction of {filepath} because files seem to be in use or already exist.")
    except Exception as e:
        print(f"Error extracting {filepath}: {e}")
        raise