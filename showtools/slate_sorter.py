'''*************************************************
content     slate_sorter

version     2.0.0
date        10-04-2026

author      Harry Shaper <harryshaper@gmail.com>

*************************************************'''

import os
import sys
import shutil
import time
from datetime import datetime

from functools import wraps
from PIL import Image, ExifTags

# Supports both:
# 1. python -m showtools.ShowTools
# 2. direct script execution during testing
try:
	from . import generate_report
	from .tools.FileSplitter.file_splitter import file_split
except ImportError:
	import generate_report
	from tools.FileSplitter.file_splitter import file_split


def timer_function(func):
	@wraps(func)
	def wrapper(*args, **kwargs):
		start_time = time.time()
		result = func(*args, **kwargs)
		end_time = time.time()
		print(f"{func.__name__} took {end_time - start_time:.4f} seconds.")
		return result
	return wrapper


# *********************************************************************#
# RULE HELPERS
def resolve_data_type_folder_and_output_root(target_folder, data_type):
	"""
	Supports both:

	1. Full shoot mode:
		target_folder / DATA_TYPE

	2. Single data type mode:
		target_folder itself is the DATA_TYPE folder

	Returns:
		(data_type_folder, output_root)
	"""
	standard_path = os.path.join(target_folder, data_type)
	if os.path.isdir(standard_path):
		return standard_path, target_folder

	target_name = os.path.basename(os.path.normpath(target_folder))
	if target_name.lower() == data_type.lower():
		output_root = os.path.dirname(os.path.normpath(target_folder))
		return target_folder, output_root

	return None, None


def get_slate_rule_map(settings_data):
	"""
	Return a dictionary of:
		data_type -> rule
	for rules marked as sort_by == SLATE.
	"""
	rule_map = {}

	for rule in settings_data.get("rename_rules", []):
		data_type = rule.get("data_type", "").strip()
		sort_by = rule.get("sort_by", "").strip().upper()

		if not data_type:
			continue

		if sort_by != "SLATE":
			continue

		rule_map[data_type] = rule

	return rule_map
	

def is_wildcard_data_type(value):
	return str(value).strip().lower() in {"*", "*all", "all"}


def get_keep_structure_rule_map(settings_data):
	"""
	Return a dictionary of:
		data_type -> rule
	for rules marked as sort_by == KEEP STRUCTURE.
	"""
	rule_map = {}

	for rule in settings_data.get("rename_rules", []):
		data_type = rule.get("data_type", "").strip()
		sort_by = rule.get("sort_by", "").strip().upper()

		if not data_type:
			continue

		if sort_by != "KEEP STRUCTURE":
			continue

		rule_map[data_type] = rule

	return rule_map


def parse_name_segments(original_name):
	"""Split an original folder name into underscore-separated segments."""
	if not original_name:
		return []

	return [segment for segment in original_name.split("_") if segment]


def format_focal_length_value(focal_raw):
	"""
	Convert EXIF values like 35, 35.0, or rational values into '35' or '35.5'.
	"""
	try:
		if isinstance(focal_raw, tuple) and len(focal_raw) == 2:
			num, den = focal_raw
			if den == 0:
				return ""
			value = float(num) / float(den)
		else:
			value = float(focal_raw)

		if value.is_integer():
			return str(int(value))

		return f"{value:.1f}".rstrip("0").rstrip(".")
	except Exception:
		return ""


def extract_focal_length_from_image(image_path):
	"""
	Read focal length metadata and return it as a string like '35mm'.
	Returns '' if unavailable.
	"""
	try:
		with Image.open(image_path) as img:
			exif = img.getexif()
			if not exif:
				return ""

			focal_raw = exif.get(ExifTags.Base.FocalLength)

			if focal_raw is None:
				try:
					exif_ifd = exif.get_ifd(ExifTags.IFD.Exif)
					focal_raw = exif_ifd.get(ExifTags.Base.FocalLength)
				except Exception:
					pass

			if focal_raw is None:
				try:
					exif_ifd = exif.get_ifd(ExifTags.IFD.Exif)
					focal_raw = exif_ifd.get(ExifTags.Base.FocalLengthIn35mmFilm)
				except Exception:
					pass

			if focal_raw is None:
				return ""

			focal_clean = format_focal_length_value(focal_raw)
			if not focal_clean:
				return ""

			return f"{focal_clean}mm"

	except Exception:
		return ""


def detect_folder_focal_length(folder_path):
	"""
	Look through files in a folder and return the first focal length found,
	formatted like '35mm'. Returns '' if nothing is found.
	"""
	if not folder_path or not os.path.isdir(folder_path):
		return ""

	preferred_ext_order = [".cr2", ".cr3", ".arw", ".dng", ".jpg", ".jpeg", ".tif", ".tiff"]
	candidate_files = []

	for file_name in os.listdir(folder_path):
		file_path = os.path.join(folder_path, file_name)

		if not os.path.isfile(file_path):
			continue

		ext = os.path.splitext(file_name)[1].lower()
		if ext in preferred_ext_order:
			priority = preferred_ext_order.index(ext)
			candidate_files.append((priority, file_path))

	candidate_files.sort(key=lambda x: x[0])

	for _, file_path in candidate_files:
		focal_value = extract_focal_length_from_image(file_path)
		if focal_value:
			return focal_value

	return ""


def build_renamed_folder_name(original_name, rule, settings_data, focal_value=""):
	"""
	Apply a rename rule to a folder name using rule + project settings.
	"""
	naming_rule = rule.get("naming_rule", "").strip()
	if not naming_rule:
		naming_rule = "{ALL}"

	# Backward compatibility for any older saved rules
	naming_rule = naming_rule.replace("{MIDDLE}", "{REST}")

	project_details = settings_data.get("project_details", {})
	segments = parse_name_segments(original_name)

	first = ""
	rest = ""
	last = ""
	all_name = original_name

	if len(segments) == 1:
		first = segments[0]

	elif len(segments) >= 2:
		first = segments[0]
		rest = "_".join(segments[1:])
		last = segments[-1]

	if not focal_value:
		focal_value = "VARIABLEmm"

	replacements = {
		"{ALL}": all_name,
		"{FIRST}": first,
		"{REST}": rest,
		"{LAST}": last,
		"{SLATE}": first,
		"{WRANGLER}": project_details.get("wrangler", "").strip(),
		"{UNIT}": project_details.get("unit", "").strip(),
		"{DATE}": datetime.now().strftime("%Y%m%d"),
		"{SHOOT_DATE}": project_details.get("shoot_date", "").replace("-", "").strip(),
		"{PROJECT}": project_details.get("project_name", "").strip(),
		"{DATA_TYPE}": rule.get("data_type", "").strip(),
		"{FOCAL}": focal_value,
	}

	new_name = naming_rule
	for token, value in replacements.items():
		new_name = new_name.replace(token, value)

	while "__" in new_name:
		new_name = new_name.replace("__", "_")

	new_name = new_name.strip("_")
	return new_name or original_name


# *********************************************************************#
# HELPERS
def is_single_data_type_input(target_folder, settings_data):
	target_name = os.path.basename(os.path.normpath(target_folder)).lower()

	for rule in settings_data.get("rename_rules", []):
		data_type = rule.get("data_type", "").strip().lower()
		if data_type and data_type == target_name:
			return True

	return False

def folder_contains_images(folder_path):
	image_extensions = {
		".jpg", ".jpeg", ".png", ".tif", ".tiff", ".exr",
		".dng", ".cr2", ".cr3", ".nef", ".arw", ".raf"
	}

	if not os.path.isdir(folder_path):
		return False

	for root, dirs, files in os.walk(folder_path):
		for file_name in files:
			ext = os.path.splitext(file_name)[1].lower()
			if ext in image_extensions:
				return True

	return False


def find_empty_data_folders(root_folder):
	"""
	Find empty capture folders inside a sorted root like:
		root_folder / SLATE / DATA_TYPE / CAPTURE_FOLDER
	"""
	empty_folders = []

	if not os.path.isdir(root_folder):
		return empty_folders

	for slate in os.listdir(root_folder):
		slate_path = os.path.join(root_folder, slate)
		if not os.path.isdir(slate_path):
			continue

		for data_type in os.listdir(slate_path):
			data_type_path = os.path.join(slate_path, data_type)
			if not os.path.isdir(data_type_path):
				continue

			for capture_folder in os.listdir(data_type_path):
				capture_path = os.path.join(data_type_path, capture_folder)
				if not os.path.isdir(capture_path):
					continue

				if not folder_contains_images(capture_path):
					empty_folders.append(capture_path)

	return empty_folders


def tag_empty_folders(empty_folders):
	renamed_paths = []

	for folder_path in empty_folders:
		parent = os.path.dirname(folder_path)
		name = os.path.basename(folder_path)

		if name.endswith("_MISSING"):
			renamed_paths.append(folder_path)
			continue

		new_name = f"{name}_MISSING"
		new_name = new_name.replace("__", "_").strip("_")

		new_path = os.path.join(parent, new_name)

		if not os.path.exists(new_path):
			os.rename(folder_path, new_path)
			renamed_paths.append(new_path)
		else:
			renamed_paths.append(folder_path)

	return renamed_paths


# *********************************************************************#
@timer_function
def sort_slate_data(target_folder, settings_data):
	"""
	Sort only data types whose rules are marked:
		sort_by = SLATE

	Supports:
	1. Full shoot folder input
	2. Single data type folder input

	Destination structure:
		output_root / SLATES / SLATE / DATA_TYPE / RENAMED_CAPTURE_FOLDER
	"""
	moves = []
	operations = []
	rule_map = get_slate_rule_map(settings_data)

	if not rule_map:
		return {
			"moves": [],
			"output_roots": set(),
			"operations": [],
		}

	source_folders = []
	output_roots = set()

	for data_type, rule in rule_map.items():
		data_type_folder, output_root = resolve_data_type_folder_and_output_root(
			target_folder,
			data_type
		)

		if not data_type_folder or not output_root:
			continue

		source_folders.append(data_type_folder)
		output_roots.add(output_root)

		slates_root = os.path.join(output_root, "SLATES")
		os.makedirs(slates_root, exist_ok=True)

		for item in os.listdir(data_type_folder):
			src_path = os.path.join(data_type_folder, item)

			if not os.path.isdir(src_path):
				continue

			slate = item.split("_")[0].upper()
			focal_value = detect_folder_focal_length(src_path)

			renamed_item = build_renamed_folder_name(
				original_name=item,
				rule=rule,
				settings_data=settings_data,
				focal_value=focal_value,
			)

			dst_path = os.path.join(
				slates_root,
				slate,
				data_type,
				renamed_item
			)

			moves.append((src_path, dst_path, rule))

	for src, dst, rule in moves:
		os.makedirs(os.path.dirname(dst), exist_ok=True)
		shutil.move(src, dst)

		operations.append({
			"type": "move",
			"from": src,
			"to": dst,
		})

		if rule.get("split_image_type", False) and os.path.isdir(dst):
			file_split(dst)

			operations.append({
				"type": "split",
				"folder": dst,
				"created_subfolders": [],
			})

	for folder in source_folders:
		if os.path.exists(folder) and not os.listdir(folder):
			os.rmdir(folder)

	return {
		"moves": moves,
		"output_roots": output_roots,
		"operations": operations,
	}

@timer_function
def process_keep_structure_data(target_folder, settings_data):
	"""
	Process data types whose rules are marked:
		sort_by = KEEP STRUCTURE

	Behavior:
	- keeps existing folder structure
	- renames capture folders in place
	- optionally splits image types inside those folders
	- supports wildcard data types: *, *all, all
	"""
	rule_map = get_keep_structure_rule_map(settings_data)

	if not rule_map:
		return {
			"processed_folders": [],
			"output_roots": set(),
			"operations": [],
		}

	processed_folders = []
	output_roots = set()
	operations = []

	wildcard_rule = None
	exact_rules = {}

	for data_type, rule in rule_map.items():
		if is_wildcard_data_type(data_type):
			wildcard_rule = rule
		else:
			exact_rules[data_type.lower()] = rule

	child_folders = [
		os.path.join(target_folder, name)
		for name in os.listdir(target_folder)
		if os.path.isdir(os.path.join(target_folder, name))
	]

	for data_type_folder in child_folders:
		data_type = os.path.basename(os.path.normpath(data_type_folder))
		data_type_key = data_type.lower()

		rule = exact_rules.get(data_type_key)

		if rule is None:
			rule = wildcard_rule

		if rule is None:
			continue

		output_root = target_folder
		output_roots.add(output_root)

		processing_rule = rule.copy()
		processing_rule["data_type"] = data_type

		# If this folder directly contains images, process it as the capture folder.
		direct_files = [
			name for name in os.listdir(data_type_folder)
			if os.path.isfile(os.path.join(data_type_folder, name))
		]

		direct_image_files = [
			name for name in direct_files
			if os.path.splitext(name)[1].lower() in {
				".jpg", ".jpeg", ".png", ".tif", ".tiff", ".exr",
				".dng", ".cr2", ".cr3", ".nef", ".arw", ".raf"
			}
		]

		if direct_image_files:
			capture_folders = [data_type_folder]
		else:
			capture_folders = [
				os.path.join(data_type_folder, item)
				for item in os.listdir(data_type_folder)
				if os.path.isdir(os.path.join(data_type_folder, item))
			]

		for src_path in capture_folders:
			item = os.path.basename(os.path.normpath(src_path))

			focal_value = detect_folder_focal_length(src_path)

			renamed_item = build_renamed_folder_name(
				original_name=item,
				rule=processing_rule,
				settings_data=settings_data,
				focal_value=focal_value,
			)

			parent_folder = os.path.dirname(src_path)
			dst_path = os.path.join(parent_folder, renamed_item)

			final_folder_path = src_path

			# Rename in place if needed
			if src_path != dst_path:
				if not os.path.exists(dst_path):
					os.rename(src_path, dst_path)
					final_folder_path = dst_path

					operations.append({
						"type": "rename_folder",
						"from": src_path,
						"to": dst_path,
					})
				else:
					final_folder_path = src_path

			# Apply split after rename
			if rule.get("split_image_type", False) and os.path.isdir(final_folder_path):
				file_split(final_folder_path)

				operations.append({
					"type": "split",
					"folder": final_folder_path,
					"created_subfolders": [],
				})

			processed_folders.append(final_folder_path)

	return {
		"processed_folders": processed_folders,
		"output_roots": output_roots,
		"operations": operations,
	}


def rename_shoot_folder(shoot_folder, rename_remove="", rename_prefix="", rename_suffix=""):
	parent_folder = os.path.dirname(shoot_folder)
	original_name = os.path.basename(shoot_folder)

	cleaned_name = original_name
	if rename_remove:
		cleaned_name = cleaned_name.replace(rename_remove, "")

	cleaned_name = cleaned_name.replace("__", "_").strip("_")

	new_shoot_name = f"{rename_prefix}{cleaned_name}{rename_suffix}"
	new_shoot_name = new_shoot_name.replace("__", "_").strip("_")

	new_shoot_path = os.path.join(parent_folder, new_shoot_name)

	if original_name == new_shoot_name:
		print("Folder name unchanged (remove/prefix/suffix result identical).")
		return shoot_folder

	if os.path.exists(new_shoot_path):
		print(f"Cannot rename. Destination already exists: {new_shoot_path}")
		return shoot_folder

	os.rename(shoot_folder, new_shoot_path)
	print(f"Folder renamed to: {new_shoot_path}")
	return new_shoot_path


def run_slate_sorter(target_folder, settings_data):
	if not target_folder or not os.path.isdir(target_folder):
		raise ValueError(f"'{target_folder}' is not a valid folder.")

	package_settings = settings_data.get("package_settings", {})
	generate_yaml = package_settings.get("generate_yaml", False)
	flag_empty_folders = package_settings.get("flag_empty_folders", False)
	create_revert_manifest = package_settings.get("create_revert_manifest", True)

	single_data_type_mode = is_single_data_type_input(target_folder, settings_data)

	slate_result = sort_slate_data(target_folder, settings_data)
	keep_result = process_keep_structure_data(target_folder, settings_data)

	output_roots = set()
	output_roots.update(slate_result.get("output_roots", set()))
	output_roots.update(keep_result.get("output_roots", set()))

	operations = []
	operations.extend(slate_result.get("operations", []))
	operations.extend(keep_result.get("operations", []))

	# Actual output root for generated structures like SLATES
	if len(output_roots) == 1:
		output_root = next(iter(output_roots))
	else:
		output_root = target_folder

	# For single data type mode, attach manifest + rename target to the selected folder
	if single_data_type_mode:
		manifest_root = target_folder
		package_rename_target = target_folder
	else:
		manifest_root = output_root
		package_rename_target = output_root

	slates_root = os.path.join(output_root, "SLATES")

	empty_folders = []
	if flag_empty_folders and not create_revert_manifest:
		# Skip empty-folder tagging for reversible sorts for now
		empty_folders.extend(find_empty_data_folders(slates_root))

		for folder_path in keep_result.get("processed_folders", []):
			if os.path.isdir(folder_path) and not folder_contains_images(folder_path):
				empty_folders.append(folder_path)

	print("\nProcessing complete.")
	return {
		"final_path": output_root,
		"manifest_root": manifest_root,
		"package_rename_target": package_rename_target,
		"empty_folders": empty_folders,
		"operations": operations,
	}


def main():
	if len(sys.argv) < 2:
		print("Usage: python slate_sorter.py <shoot_folder_path>")
		sys.exit(1)

	shoot_folder = sys.argv[1]

	settings_data = {
		"project_details": {
			"project_name": "TEST_SHOW",
			"shoot_date": "2026-04-10",
			"wrangler": "Harry",
			"unit": "Main",
		},
		"package_settings": {
			"rename_package": True,
			"prefix": "",
			"suffix": "_sorted",
			"generate_yaml": False,
			"flag_empty_folders": False,
		},
		"rename_rules": [
			{
				"name": "HDRI",
				"data_type": "HDRI",
				"sort_by": "SLATE",
				"split_image_type": True,
				"delete_empty_folders": False,
				"naming_rule": "{DATE}_{SLATE}_{FOCAL}_{REST}",
			}
		]
	}

	try:
		run_slate_sorter(shoot_folder, settings_data)
	except Exception as error:
		print(f"Error: {error}")
		sys.exit(1)


if __name__ == "__main__":
	main()