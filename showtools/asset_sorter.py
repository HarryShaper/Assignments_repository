'''*************************************************
content     asset_sorter

version     1.0.0
date        12-04-2026

author      Harry Shaper <harryshaper@gmail.com>

*************************************************'''

import os
import shutil
import time

from datetime import datetime
from functools import wraps
from PIL import Image, ExifTags

# Supports both:
# 1. python -m showtools.ShowTools
# 2. direct script execution during testing
try:
	from .tools.FileSplitter.file_splitter import file_split
except ImportError:
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

def get_asset_rule_map(settings_data):
	"""
	Return a dictionary of:
		data_type -> rule
	for rules marked as sort_by == ASSET.
	"""
	rule_map = {}

	for rule in settings_data.get("rename_rules", []):
		data_type = rule.get("data_type", "").strip()
		sort_by = rule.get("sort_by", "").strip().upper()

		if not data_type:
			continue

		if sort_by != "ASSET":
			continue

		rule_map[data_type] = rule

	return rule_map


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


def parse_name_segments(original_name):
	if not original_name:
		return []

	return [segment for segment in original_name.split("_") if segment]


# *********************************************************************#
# FOCAL HELPERS
def format_focal_length_value(focal_raw):
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


# *********************************************************************#
# ASSET PARSING
ASSET_TYPE_ALIASES = {
	"CHR": "chr",
	"CHAR": "chr",
	"CHARACTER": "chr",

	"CRT": "crt",
	"CREATURE": "crt",

	"PRP": "prp",
	"PROP": "prp",

	"ENV": "env",
	"ENVIRONMENT": "env",
	"SET": "env",

	"VEH": "veh",
	"VEHICLE": "veh",
}


def normalize_asset_type(asset_type_token):
	if not asset_type_token:
		return None

	return ASSET_TYPE_ALIASES.get(asset_type_token.strip().upper())

def parse_asset_name(folder_name):
	"""
	Strict asset parsing.

	Expected:
		ASSETTYPE_ASSETNAME
		ASSETTYPE_ASSETNAME_MOREWORDS

	Examples:
		CHR_SPIDERMAN
		CHR_SPIDERMAN_BOOTS
		vehicle_batmobile

	Returns:
		{
			"asset_type": "chr",
			"asset_name": "spiderman_boots",
		}
	or None if invalid.
	"""
	parts = [p for p in folder_name.split("_") if p]

	if len(parts) < 2:
		return None

	asset_type = normalize_asset_type(parts[0])
	if not asset_type:
		return None

	asset_name = "_".join(part.lower() for part in parts[1:])

	return {
		"asset_type": asset_type.lower(),
		"asset_name": asset_name,
	}

# *********************************************************************#
# RENAMING
def build_renamed_folder_name(original_name, rule, settings_data, focal_value="", asset_info=None):
	naming_rule = rule.get("naming_rule", "").strip()
	if not naming_rule:
		naming_rule = "{ALL}"

	# Backward compatibility
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

	asset_type = ""
	asset_name = ""

	if asset_info:
		asset_type = asset_info.get("asset_type", "")
		asset_name = asset_info.get("asset_name", "")

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
		"{ASSET_TYPE}": asset_type,
		"{ASSET_NAME}": asset_name,
		"{ROOT_ASSET}": asset_name,
	}

	new_name = naming_rule
	for token, value in replacements.items():
		new_name = new_name.replace(token, value)

	while "__" in new_name:
		new_name = new_name.replace("__", "_")

	new_name = new_name.strip("_")
	return new_name or original_name


# *********************************************************************#
# EMPTY FOLDER HELPERS
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


def find_empty_asset_folders(root_folder):
	"""
	Find empty capture folders inside:
		root_folder / ASSETS / ASSET_TYPE / ASSET_NAME / DATA_TYPE
	"""
	empty_folders = []

	assets_root = os.path.join(root_folder, "ASSETS")
	if not os.path.isdir(assets_root):
		return empty_folders

	for asset_type in os.listdir(assets_root):
		asset_type_path = os.path.join(assets_root, asset_type)
		if not os.path.isdir(asset_type_path):
			continue

		for asset_name in os.listdir(asset_type_path):
			asset_name_path = os.path.join(asset_type_path, asset_name)
			if not os.path.isdir(asset_name_path):
				continue

			for data_type in os.listdir(asset_name_path):
				data_type_path = os.path.join(asset_name_path, data_type)
				if not os.path.isdir(data_type_path):
					continue

				if not folder_contains_images(data_type_path):
					empty_folders.append(data_type_path)

	return empty_folders


# *********************************************************************#
@timer_function
@timer_function
def sort_asset_data(target_folder, settings_data):
	"""
	Sort only data types whose rules are marked:
		sort_by = ASSET

	Destination structure:
		output_root / ASSETS / ASSET_TYPE / ASSET_NAME / DATA_TYPE
	"""
	operations = []
	rule_map = get_asset_rule_map(settings_data)

	if not rule_map:
		return {
			"output_roots": set(),
			"operations": [],
			"invalid_asset_folders": [],
		}

	output_roots = set()
	invalid_asset_folders = []

	for data_type, rule in rule_map.items():
		data_type_folder, output_root = resolve_data_type_folder_and_output_root(
			target_folder,
			data_type
		)

		if not data_type_folder or not output_root:
			continue

		output_roots.add(output_root)

		for item in os.listdir(data_type_folder):
			src_path = os.path.join(data_type_folder, item)

			if not os.path.isdir(src_path):
				continue

			asset_info = parse_asset_name(item)
			if not asset_info:
				invalid_asset_folders.append(src_path)
				continue

			focal_value = detect_folder_focal_length(src_path)

			renamed_item = build_renamed_folder_name(
				original_name=item,
				rule=rule,
				settings_data=settings_data,
				focal_value=focal_value,
				asset_info=asset_info,
			)

			# Base asset structure
			dst_base = os.path.join(
				output_root,
				"ASSETS",
				asset_info["asset_type"],
				asset_info["asset_name"],
				data_type.lower()
			)

			# If naming rule changes the leaf folder name, nest it one level deeper
			if renamed_item and renamed_item != item:
				dst_path = os.path.join(dst_base, renamed_item)
			else:
				dst_path = dst_base

			os.makedirs(os.path.dirname(dst_path), exist_ok=True)
			shutil.move(src_path, dst_path)

			operations.append({
				"type": "move",
				"from": src_path,
				"to": dst_path,
			})

			if rule.get("split_image_type", False) and os.path.isdir(dst_path):
				file_split(dst_path)

				operations.append({
					"type": "split",
					"folder": dst_path,
					"created_subfolders": [],
				})

		# Remove empty original data type folder if possible
		if os.path.exists(data_type_folder) and not os.listdir(data_type_folder):
			os.rmdir(data_type_folder)

	return {
		"output_roots": output_roots,
		"operations": operations,
		"invalid_asset_folders": invalid_asset_folders,
	}


def run_asset_sorter(target_folder, settings_data):
	if not target_folder or not os.path.isdir(target_folder):
		raise ValueError(f"'{target_folder}' is not a valid folder.")

	package_settings = settings_data.get("package_settings", {})
	flag_empty_folders = package_settings.get("flag_empty_folders", False)
	create_revert_manifest = package_settings.get("create_revert_manifest", True)

	sort_result = sort_asset_data(target_folder, settings_data)

	output_roots = sort_result.get("output_roots", set())
	operations = sort_result.get("operations", [])
	invalid_asset_folders = sort_result.get("invalid_asset_folders", [])

	if len(output_roots) == 1:
		final_root = next(iter(output_roots))
	else:
		final_root = target_folder

	empty_folders = []
	if flag_empty_folders and not create_revert_manifest:
		empty_folders = find_empty_asset_folders(final_root)

	return {
		"final_path": final_root,
		"empty_folders": empty_folders,
		"operations": operations,
		"invalid_asset_folders": invalid_asset_folders,
	}