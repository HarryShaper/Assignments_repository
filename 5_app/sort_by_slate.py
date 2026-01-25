'''*************************************************
content     Tool Demo

version     0.0.2
date        25-12-2025

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
        unique_slate = item.split("_")
        if unique_slate[0] not in SLATE_LIST:
            SLATE_LIST.append(unique_slate[0])
    

#LOOK THROUGH ALL SHOOT DATA
def get_slates():
    for item in path_items:
        file_path = SHOOT_FOLDER + "\\" + item
        #print(file_path)
        update_slate_list(file_path)

#Makes all necessary slate folder
def make_slate_folders():

    list = get_shoot_data_types()   #Gets types of shoot data listed
    for slate in SLATE_LIST:
        slate_path = SHOOT_FOLDER + "\\" + slate.upper() 
        os.mkdir(slate_path)    #Makes a slate folder 

        for sub_folder in list:
            subfolder_path = os.path.join(slate_path, sub_folder)
            os.mkdir(subfolder_path)
        
#Moves folders to their correct file path by data type and slate
def sort_data():
    moves = []
    source_folders = set(ORIGINAL_DATA_FOLDERS)

    # Scan through each shoot data type (HDRI / PANO / TEXTURE / etc)
    for data_type_folder in define_shoot_data():
        data_type = os.path.basename(data_type_folder)

        for item in os.listdir(data_type_folder):
            src_path = os.path.join(data_type_folder, item)

            # --- CHANGE: ensure we only process folders ---
            if not os.path.isdir(src_path):
                continue

            slate = item.split("_")[0].upper()

            # --- CHANGE: destination now uses slate, not full folder name ---
            dst_path = os.path.join(
                SHOOT_FOLDER,
                slate,
                data_type,
                item  
            )

            moves.append((src_path, dst_path))

    # Move items
    for src, dst in moves:
        # --- CHANGE: only create parent directories ---
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        shutil.move(src, dst)

    # Clear original folders
    for folder in source_folders:
        if os.path.exists(folder) and not os.listdir(folder):
            os.rmdir(folder)

        

get_slates()
make_slate_folders()
sort_data()