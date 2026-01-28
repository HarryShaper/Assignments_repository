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
#Fetch "generate_report.py" location
#*********************************************************************#

#Get this files folder directory
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

#Add this path to the system path so It can find report generator
if SCRIPT_DIR not in sys.path:
    sys.path.append(SCRIPT_DIR)

#Fetches generate_report.py // Now usable
import generate_report

#*********************************************************************#
#DYNAMICALLY FETCH SELECTED FOLDER - For Right-Click / Send To
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
#*********************************************************************#

SLATE_LIST = []
DATA_TYPES = []
ORIGINAL_DATA_FOLDERS = []

#Looks for folders only, not files
for f in os.listdir(SHOOT_FOLDER):
    if os.path.isdir(os.path.join(SHOOT_FOLDER, f)):
        ORIGINAL_DATA_FOLDERS.append(os.path.join(SHOOT_FOLDER, f))


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

#*********************************************************************#
#Create report file ?
#*********************************************************************#

answer = input("Would you like to generate a YAML report (Y/N): ").strip().lower()

if answer == "y":
    try:
        import generate_report
        generate_report.generate_report(SHOOT_FOLDER)
    except ModuleNotFoundError:
        print("Error: generate_report.py not found or PyYAML not installed.")

#*********************************************************************#
#Rename folder to "_sorted", marking it ready for ingestion
#*********************************************************************#

rename = True #Users can set this to False if they don't want renaming to happen

if rename:
    parent_folder = os.path.dirname(SHOOT_FOLDER)
    new_shoot_name = os.path.basename(SHOOT_FOLDER) + "_sorted"
    new_shoot_path = os.path.join(parent_folder, new_shoot_name)

    if not os.path.exists(new_shoot_path):
        os.rename(SHOOT_FOLDER, new_shoot_path)
        print(f"Folder renamed to: {new_shoot_path}")
    else:
        print(f"Folder already has _sorted: {new_shoot_path}")

print("\nProcessing complete. Press Enter to exit.")
input()  #Keeps terminal open until user presses Enter