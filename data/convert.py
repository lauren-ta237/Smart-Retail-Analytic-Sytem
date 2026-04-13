import os
import json
from PIL import Image
from collections import defaultdict

def convert_coco_to_yolo(raw_dir, processed_dir, class_mapping):
    coco_file = None

    for root, _, files in os.walk(raw_dir):
        for file in files:
            if file.endswith('.json'):
                coco_file = os.path.join(root, file)

    if not coco_file:
        return

    with open(coco_file) as f:
        data = json.load(f)

    image_map = {img['id']: img['file_name'] for img in data['images']}
    annotations = defaultdict(list)

    for ann in data['annotations']:
        if ann['category_id'] in class_mapping:
            annotations[ann['image_id']].append(ann)

    for img_id, anns in annotations.items():
        img_file = image_map[img_id]
        img_path = os.path.join(processed_dir, img_file)

        if not os.path.exists(img_path):
            continue

        with Image.open(img_path) as img:
            w, h = img.size

        label_path = os.path.join(processed_dir, img_file.replace('.jpg', '.txt'))

        with open(label_path, 'w') as f:
            for ann in anns:
                x, y, bw, bh = ann['bbox']
                xc = (x + bw/2) / w
                yc = (y + bh/2) / h
                bw /= w
                bh /= h

                f.write(f"{class_mapping[ann['category_id']]} {xc} {yc} {bw} {bh}\n")