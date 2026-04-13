import os

def create_data_yaml(output_dir, class_names):
    yaml_path = os.path.join(output_dir, "data.yaml")

    content = f"""
train: {output_dir}/images
val: {output_dir}/images

nc: {len(class_names)}
names: {class_names}
"""

    with open(yaml_path, "w") as f:
        f.write(content)