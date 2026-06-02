'''*************************************************
content     FileSplitter

version     0.0.2
date        24-03-2026

author      Harry Shaper <harryshaper@gmail.com>

*************************************************'''

import os
import sys
import shutil


def get_image_paths(folder_path):
    return [
        os.path.join(folder_path, image)
        for image in os.listdir(folder_path)
        if not os.path.isdir(os.path.join(folder_path, image))
    ]


def get_type(image_name):
    file_type = os.path.splitext(image_name)[-1]
    return file_type[1:].lower()


def update_types_list(folder_path):
    image_types = set()

    for image in os.listdir(folder_path):
        source_path = os.path.join(folder_path, image)

        if not os.path.isdir(source_path):
            image_ext = get_type(image)
            if image_ext:
                image_types.add(image_ext)

    return image_types


def make_image_folders(folder_path, image_types):
    for ext in image_types:
        new_folder = os.path.join(folder_path, ext.upper())
        os.makedirs(new_folder, exist_ok=True)


def move_images(folder_path):
    for image in os.listdir(folder_path):
        source_path = os.path.join(folder_path, image)

        if not os.path.isdir(source_path):
            extension = get_type(image)
            destination_path = os.path.join(folder_path, extension.upper(), image)
            shutil.move(source_path, destination_path)


def file_split(folder_path):
    """
    Split files inside folder_path into subfolders by extension.
    Example:
        image001.cr2 -> CR2/image001.cr2
        image001.jpg -> JPG/image001.jpg
    """
    if not folder_path or not os.path.isdir(folder_path):
        raise ValueError(f"'{folder_path}' is not a valid folder.")

    print(f"FileSplitter running on folder: {folder_path}")

    image_types = update_types_list(folder_path)
    make_image_folders(folder_path, image_types)
    move_images(folder_path)


def main():
    if len(sys.argv) < 2:
        print("Usage: file_splitter.py <folder_path>")
        sys.exit(1)

    folder_path = sys.argv[1]

    try:
        file_split(folder_path)
    except Exception as error:
        print(f"Error: {error}")
        sys.exit(1)


if __name__ == "__main__":
    main()