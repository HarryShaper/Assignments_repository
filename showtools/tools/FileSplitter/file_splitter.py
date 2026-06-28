'''*************************************************
content     FileSplitter

version     0.0.3
date        24-03-2026

author      Harry Shaper <harryshaper@gmail.com>

*************************************************'''

import os
import sys
import shutil


RAW_EXTENSIONS = {
    "arw",
    "cr2",
    "cr3",
    "dng",
    "nef",
    "raf",
    "rw2",
    "orf",
    "raw",
}


def get_image_paths(folder_path):
    return [
        os.path.join(folder_path, image)
        for image in os.listdir(folder_path)
        if not os.path.isdir(os.path.join(folder_path, image))
    ]


def get_type(image_name):
    file_type = os.path.splitext(image_name)[-1]
    return file_type[1:].lower()


def get_split_folder_name(image_name):
    extension = get_type(image_name)

    if extension in RAW_EXTENSIONS:
        return "raw"

    return extension


def update_types_list(folder_path):
    image_types = set()

    for image in os.listdir(folder_path):
        source_path = os.path.join(folder_path, image)

        if not os.path.isdir(source_path):
            folder_name = get_split_folder_name(image)
            if folder_name:
                image_types.add(folder_name)

    return image_types


def make_image_folders(folder_path, image_types):
    for folder_name in image_types:
        new_folder = os.path.join(folder_path, folder_name)
        os.makedirs(new_folder, exist_ok=True)


def move_images(folder_path):
    for image in os.listdir(folder_path):
        source_path = os.path.join(folder_path, image)

        if not os.path.isdir(source_path):
            folder_name = get_split_folder_name(image)
            if not folder_name:
                continue

            destination_path = os.path.join(folder_path, folder_name, image)
            shutil.move(source_path, destination_path)


def file_split(folder_path):
    """
    Split files inside folder_path into subfolders by type.

    Examples:
        image001.cr2 -> raw/image001.cr2
        image001.cr3 -> raw/image001.cr3
        image001.arw -> raw/image001.arw
        image001.jpg -> jpg/image001.jpg
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