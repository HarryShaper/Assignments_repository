'''*************************************************
content     Tool Demo

version     0.0.1
date        14-12-2025

author      Harry Shaper <harryshaper@gmail.com>

*************************************************'''
#IMPORTS
import os
import shutil
import sys


#*********************************************************************#
#FETCH SELECTED FOLDER
#*********************************************************************#

if len(sys.argv) < 2:
    print("Usage: python sort_shoot.py <shoot_folder_path>")
    sys.exit(1)

SHOOT_FOLDER = sys.argv[1]

if not os.path.isdir(SHOOT_FOLDER):
    print(f"Error: '{SHOOT_FOLDER}' is not a valid folder.")
    sys.exit(1)

#*********************************************************************#    

#CONSTANTS
#SHOOT_FOLDER = r"D:\VFX\assets_and_courses\courses\Advanced_python_course\course_notes\shoot_day_001"
SLATE_LIST = []
DATA_TYPES = []
ORIGINAL_DATA_FOLDERS = [
    os.path.join(SHOOT_FOLDER, f)
    for f in os.listdir(SHOOT_FOLDER)
    if os.path.isdir(os.path.join(SHOOT_FOLDER, f))
]

#CONTENTS OF SHOOT_FOLDER
path_items = os.listdir(SHOOT_FOLDER)

#Creates a list of each shoot data path (HDRI/PANO/SET-REF/ETC)
def define_shoot_data():
    return [
        os.path.join(SHOOT_FOLDER, folder)
        for folder in os.listdir(SHOOT_FOLDER)
        if os.path.isdir(os.path.join(SHOOT_FOLDER, folder))
    ]

def get_shoot_data_types():
    define_shoot_data()
    return DATA_TYPES

#MAKE SLATE LIST
def update_slate_list(folder):
    data_set_folder = os.listdir(folder)
    for item in data_set_folder:
        if item not in SLATE_LIST:
            SLATE_LIST.append(item)

#LOOK THROUGH ALL SHOOT DATA
def get_slates():
    for item in path_items:
        file_path = SHOOT_FOLDER + "\\" + item
        #print(file_path)
        update_slate_list(file_path)

    #print(SLATE_LIST)

#Makes all necessary slate folder
def make_slate_folders():

    list = get_shoot_data_types()   #Gets types of shoot data listed
    for slate in SLATE_LIST:
        slate_path = SHOOT_FOLDER + "\\" + slate 
        os.mkdir(slate_path)    #Makes a slate folder 

        for sub_folder in list:
            subfolder_path = os.path.join(slate_path, sub_folder)
            os.mkdir(subfolder_path)
        
#Moves folders to their correct file path by data type and slate
def sort_data():
    moves = []
    source_folders = set(ORIGINAL_DATA_FOLDERS)

    #Scan through items
    for folder in define_shoot_data():
        current_data_type = os.path.basename(folder)
        source_folders.add(folder)

        for sub_folder in os.listdir(folder):
            current_path = os.path.join(folder, sub_folder)
            destination = os.path.join(
                SHOOT_FOLDER,
                sub_folder,
                current_data_type
            )

            moves.append((current_path, destination))

    #Move items
    for src, dst in moves:
        os.makedirs(dst, exist_ok=True)
        shutil.move(src, dst)

    #Clear original folders
    for folder in source_folders:
        if not os.listdir(folder):
            print(f"Removing empty folder: {folder}")
            os.rmdir(folder)
        else:
            print(f"Skipping (not empty): {folder} -> {os.listdir(folder)}")

get_slates()
make_slate_folders()
sort_data()