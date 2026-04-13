
import os
import shutil

def merge_datasets(dataset_names, base_dir, output_name):
    merged_dir = os.path.join(base_dir, "processed", output_name)
    images_dir = os.path.join(merged_dir, "images")
    labels_dir = os.path.join(merged_dir, "labels")

    os.makedirs(images_dir, exist_ok=True)
    os.makedirs(labels_dir, exist_ok=True)

    counter = 0

    for dataset in dataset_names:
        dataset_path = os.path.join(base_dir, "processed", dataset)

        for file in os.listdir(dataset_path):
            if file.endswith('.jpg'):
                src = os.path.join(dataset_path, file)
                new_name = f"{counter:06d}.jpg"

                shutil.copy2(src, os.path.join(images_dir, new_name))

                label_src = src.replace('.jpg', '.txt')
                if os.path.exists(label_src):
                    shutil.copy2(label_src, os.path.join(labels_dir, f"{counter:06d}.txt"))

                counter += 1