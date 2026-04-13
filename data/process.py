import os
import shutil

IMAGE_EXTS = ['.jpg', '.jpeg', '.png']
VIDEO_EXTS = ['.mp4', '.avi', '.mov']

def process_images(raw_dir, processed_dir):
    for root, _, files in os.walk(raw_dir):
        for file in files:
            if file.lower().endswith(tuple(IMAGE_EXTS)):
                src = os.path.join(root, file)
                dst = os.path.join(processed_dir, file)
                os.makedirs(processed_dir, exist_ok=True)
                shutil.copy2(src, dst)


def process_videos(raw_dir, videos_dir):
    for root, _, files in os.walk(raw_dir):
        for file in files:
            if file.lower().endswith(tuple(VIDEO_EXTS)):
                src = os.path.join(root, file)
                dst = os.path.join(videos_dir, file)
                os.makedirs(videos_dir, exist_ok=True)
                shutil.copy2(src, dst)