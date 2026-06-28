'''*************************************************
content     ShowTools

version     0.0.1
date        23-03-2026

author      Harry Shaper <harryshaper@gmail.com>

*************************************************'''

import os
import sys
import shutil
import webbrowser
import yaml
import urllib.parse

from datetime import datetime
from pathlib import Path
from Qt import QtWidgets, QtGui, QtCore, QtCompat
from Qt.QtCore import QDate
from Qt.QtWidgets import QFileDialog
from Qt.QtGui import QStandardItemModel, QStandardItem
from PIL import Image, ExifTags

try:
	from .resources import resources_rc
	from .slate_sorter import run_slate_sorter, tag_empty_folders, rename_shoot_folder
	from .asset_sorter import run_asset_sorter
	from . import generate_report
except ImportError:
	from resources import resources_rc
	from slate_sorter import run_slate_sorter, tag_empty_folders, rename_shoot_folder
	from .asset_sorter import run_asset_sorter
	import generate_report
	


TITLE = Path(__file__).stem
CURRENT_PATH = Path(__file__).resolve().parent
ROOT_DIR = CURRENT_PATH.parent

ICONS_DIR = ROOT_DIR / "assets" / "Icons"
UI_PATH = CURRENT_PATH / "ui" / "ShowTools.ui"

APP_NAME = "ShowTools"

# ----------------------------------------------------------------------
# Bundled config shipped with the application
# ----------------------------------------------------------------------

BUNDLED_CONFIG_DIR = ROOT_DIR / "config"
BUNDLED_PIPELINE_PROFILES_PATH = BUNDLED_CONFIG_DIR / "Pipeline_profiles"
BUNDLED_SHOW_DEFAULTS_DIR = BUNDLED_CONFIG_DIR / "Show_defaults"

# ----------------------------------------------------------------------
# User-writable config location
# ----------------------------------------------------------------------

def get_user_app_data_dir():
	if sys.platform == "win32":
		base_dir = os.environ.get("LOCALAPPDATA")
		if base_dir:
			return Path(base_dir) / APP_NAME

		return Path.home() / "AppData" / "Local" / APP_NAME

	if sys.platform == "darwin":
		return Path.home() / "Library" / "Application Support" / APP_NAME

	return Path.home() / f".{APP_NAME.lower()}"

USER_APP_DATA_DIR = get_user_app_data_dir()

PIPELINE_PROFILES_PATH = USER_APP_DATA_DIR / "Pipeline_profiles"
SHOW_DEFAULTS_DIR = USER_APP_DATA_DIR / "Show_defaults"
STARTUP_PROFILE_PATH = SHOW_DEFAULTS_DIR / "startup_profile.yaml"

# Default show settings file loaded on startup
SELECTED_DEFAULT_SETTINGS = "show_default.yaml"

def icon_path(name):
	return str(ICONS_DIR / f"{name}.png")


# ******************************************************************************
# CLASSES

#DIALOGUES
class CustomMessageDialog(QtWidgets.QDialog):
	def __init__(self, title, heading, detail="", sub_detail="", parent=None):
		super().__init__(parent)

		self.setWindowTitle(title)
		self.setWindowIcon(QtGui.QIcon(icon_path("logo")))
		self.setModal(True)
		self.setFixedSize(430, 165)

		self.setStyleSheet("""
			QDialog {
				background-color: #2f2f2f;
			}

			QLabel {
				background-color: transparent;
			}

			QLabel#headingLabel {
				color: #d8a106;
				font-size: 16px;
				font-weight: 600;
			}

			QLabel#detailLabel {
				color: #f2f2f2;
				font-size: 13px;
				font-weight: 400;
			}

			QLabel#subDetailLabel {
				color: #bfbfbf;
				font-size: 11px;
				font-weight: 400;
			}

			QPushButton {
				background-color: #c99700;
				color: black;
				border: none;
				padding: 5px 14px;
				min-width: 72px;
				min-height: 30px;
				font-size: 12px;
				font-weight: 500;
			}

			QPushButton:hover {
				background-color: #d8a106;
			}

			QPushButton:pressed {
				background-color: #b88705;
			}
		""")

		# SIZING
		main_layout = QtWidgets.QVBoxLayout(self)
		main_layout.setContentsMargins(24, 18, 24, 18)
		main_layout.setSpacing(8)

		# HEADINGS
		self.heading_label = QtWidgets.QLabel(heading)
		self.heading_label.setObjectName("headingLabel")
		self.heading_label.setAlignment(QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter)
		main_layout.addWidget(self.heading_label)

		if detail:
			self.detail_label = QtWidgets.QLabel(detail)
			self.detail_label.setObjectName("detailLabel")
			self.detail_label.setWordWrap(False)
			self.detail_label.setAlignment(QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter)
			main_layout.addWidget(self.detail_label)

		if sub_detail:
			self.sub_detail_label = QtWidgets.QLabel(sub_detail)
			self.sub_detail_label.setObjectName("subDetailLabel")
			self.sub_detail_label.setWordWrap(True)
			self.sub_detail_label.setAlignment(QtCore.Qt.AlignLeft | QtCore.Qt.AlignTop)
			main_layout.addWidget(self.sub_detail_label)

		main_layout.addStretch()

		button_layout = QtWidgets.QHBoxLayout()
		button_layout.addStretch()

		self.ok_button = QtWidgets.QPushButton("OK")
		self.ok_button.clicked.connect(self.accept)
		button_layout.addWidget(self.ok_button)

		main_layout.addLayout(button_layout)

class EmptyFoldersDialog(QtWidgets.QDialog):
	def __init__(self, empty_folders, parent=None):
		super().__init__(parent)

		self.setWindowTitle("Empty Folders Detected")
		self.setWindowIcon(QtGui.QIcon(icon_path("logo")))
		self.setModal(True)
		self.setFixedSize(520, 320)

		self.setStyleSheet("""
			QDialog {
				background-color: #2f2f2f;
			}
			QLabel {
				color: #ededed;
				background: transparent;
			}
			QLabel#headingLabel {
				color: #d8a106;
				font-size: 16px;
				font-weight: 600;
			}
			QTextEdit {
				background-color: #1f1f1f;
				color: #ededed;
				border: 1px solid #4a4a4a;
				padding: 6px;
			}
			QPushButton {
				background-color: #c99700;
				color: black;
				border: none;
				padding: 5px 14px;
				min-width: 100px;
				min-height: 30px;
				font-size: 12px;
				font-weight: 500;
			}
			QPushButton:hover {
				background-color: #d8a106;
			}
			QPushButton:pressed {
				background-color: #b88705;
			}
		""")

		layout = QtWidgets.QVBoxLayout(self)
		layout.setContentsMargins(24, 18, 24, 18)
		layout.setSpacing(10)

		heading = QtWidgets.QLabel("Empty Folders Detected")
		heading.setObjectName("headingLabel")
		layout.addWidget(heading)

		detail = QtWidgets.QLabel(
			"The following folders contain no image files.\n"
			"Continue export to tag them with _MISSING, or go back to review them."
		)
		detail.setWordWrap(True)
		layout.addWidget(detail)

		folder_list = QtWidgets.QTextEdit()
		folder_list.setReadOnly(True)
		folder_list.setText("\n".join(empty_folders))
		layout.addWidget(folder_list)

		button_row = QtWidgets.QHBoxLayout()
		button_row.addStretch()

		self.back_button = QtWidgets.QPushButton("Go Back")
		self.back_button.clicked.connect(self.reject)
		button_row.addWidget(self.back_button)

		self.continue_button = QtWidgets.QPushButton("Continue Export")
		self.continue_button.clicked.connect(self.accept)
		button_row.addWidget(self.continue_button)

		layout.addLayout(button_row)

class ConfirmActionDialog(QtWidgets.QDialog):
	def __init__(self, title, heading, detail="", sub_detail="", confirm_text="Delete", parent=None):
		super().__init__(parent)

		self.setWindowTitle(title)
		self.setWindowIcon(QtGui.QIcon(icon_path("logo")))
		self.setModal(True)
		self.setFixedSize(430, 175)

		self.setStyleSheet("""
			QDialog {
				background-color: #2f2f2f;
			}

			QLabel {
				background-color: transparent;
			}

			QLabel#headingLabel {
				color: #d8a106;
				font-size: 16px;
				font-weight: 600;
			}

			QLabel#detailLabel {
				color: #f2f2f2;
				font-size: 13px;
				font-weight: 400;
			}

			QLabel#subDetailLabel {
				color: #bfbfbf;
				font-size: 11px;
				font-weight: 400;
			}

			QPushButton {
				background-color: #c99700;
				color: black;
				border: none;
				padding: 5px 14px;
				min-width: 72px;
				min-height: 30px;
				font-size: 12px;
				font-weight: 500;
			}

			QPushButton:hover {
				background-color: #d8a106;
			}

			QPushButton:pressed {
				background-color: #b88705;
			}

			QPushButton#btn_cancel {
				background-color: #4a4a4a;
				color: #ededed;
			}

			QPushButton#btn_cancel:hover {
				background-color: #5a5a5a;
			}

			QPushButton#btn_cancel:pressed {
				background-color: #3a3a3a;
			}
		""")

		main_layout = QtWidgets.QVBoxLayout(self)
		main_layout.setContentsMargins(24, 18, 24, 18)
		main_layout.setSpacing(8)

		self.heading_label = QtWidgets.QLabel(heading)
		self.heading_label.setObjectName("headingLabel")
		self.heading_label.setAlignment(QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter)
		main_layout.addWidget(self.heading_label)

		if detail:
			self.detail_label = QtWidgets.QLabel(detail)
			self.detail_label.setObjectName("detailLabel")
			self.detail_label.setWordWrap(True)
			self.detail_label.setAlignment(QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter)
			main_layout.addWidget(self.detail_label)

		if sub_detail:
			self.sub_detail_label = QtWidgets.QLabel(sub_detail)
			self.sub_detail_label.setObjectName("subDetailLabel")
			self.sub_detail_label.setWordWrap(True)
			self.sub_detail_label.setAlignment(QtCore.Qt.AlignLeft | QtCore.Qt.AlignTop)
			main_layout.addWidget(self.sub_detail_label)

		main_layout.addStretch()

		button_layout = QtWidgets.QHBoxLayout()
		button_layout.addStretch()

		self.cancel_button = QtWidgets.QPushButton("Cancel")
		self.cancel_button.setObjectName("btn_cancel")
		self.cancel_button.clicked.connect(self.reject)
		button_layout.addWidget(self.cancel_button)

		self.delete_button = QtWidgets.QPushButton(confirm_text)
		self.delete_button.clicked.connect(self.accept)
		button_layout.addWidget(self.delete_button)

		main_layout.addLayout(button_layout)

#RULE ITEMS
class RuleListItemWidget(QtWidgets.QWidget):
	def __init__(self, text="", parent=None):
		super().__init__(parent)

		self.setObjectName("ruleListItemWidget")

		# Left side spacer to balance the delete icon area on the right
		self.left_spacer = QtWidgets.QWidget()
		self.left_spacer.setFixedWidth(22)

		self.label = QtWidgets.QLabel(text)
		self.label.setObjectName("label_ruleItem")
		self.label.setAlignment(QtCore.Qt.AlignCenter)

		# Right side fixed container
		self.right_container = QtWidgets.QWidget()
		self.right_container.setFixedWidth(22)

		right_layout = QtWidgets.QHBoxLayout(self.right_container)
		right_layout.setContentsMargins(0, 0, 0, 0)
		right_layout.setSpacing(0)

		self.btn_delete = QtWidgets.QPushButton()
		self.btn_delete.setObjectName("btn_ruleDelete")
		self.btn_delete.setFixedSize(18, 18)
		self.btn_delete.setIconSize(QtCore.QSize(12, 12))
		self.btn_delete.setCursor(QtCore.Qt.PointingHandCursor)
		self.btn_delete.setIcon(QtGui.QIcon(icon_path("trash_icon")))
		self.btn_delete.hide()

		right_layout.addWidget(self.btn_delete, 0, QtCore.Qt.AlignCenter)

		layout = QtWidgets.QHBoxLayout(self)
		layout.setContentsMargins(10, 2, 10, 2)
		layout.setSpacing(6)

		layout.addWidget(self.left_spacer, 0)
		layout.addWidget(self.label, 1)
		layout.addWidget(self.right_container, 0)

		self.set_selected(False)

	def set_text(self, text):
		self.label.setText(text)

	def set_selected(self, selected):
		self.btn_delete.setVisible(selected)
		self.label.setProperty("selectedRule", selected)
		self.label.style().unpolish(self.label)
		self.label.style().polish(self.label)

#CENTRE DELEGATE
class CenteredItemDelegate(QtWidgets.QStyledItemDelegate):
	def initStyleOption(self, option, index):
		super().initStyleOption(option, index)
		option.displayAlignment = QtCore.Qt.AlignCenter

#WRANGLER DIALOGUE BOX
class WranglerDialog(QtWidgets.QDialog):

	def __init__(
		self,
		items,
		title_text="Manage Items",
		subtitle_text="Add, rename, or remove items for this show profile.",
		add_dialog_title="Add Item",
		add_dialog_label="Item Name:",
		parent=None
	):
		super().__init__(parent)

		self.title_text = title_text
		self.subtitle_text = subtitle_text
		self.add_dialog_title = add_dialog_title
		self.add_dialog_label = add_dialog_label

		self.setWindowTitle(title_text)
		self.setWindowIcon(QtGui.QIcon(icon_path("logo")))
		self.setModal(True)
		self.setFixedSize(420, 360)

		self.setStyleSheet("""
			QDialog {
				background-color: #2f2f2f;
			}

			QLabel {
				background: transparent;
				color: #ededed;
			}

			QLabel#dialogTitle {
				color: #f0b000;
				font-size: 15pt;
				font-weight: 700;
			}

			QLabel#dialogSubtitle {
				color: #bdbdbd;
				font-size: 9pt;
			}

			QListWidget {
				background-color: #1f1f1f;
				color: #ededed;
				border: 1px solid #4a4a4a;
				outline: none;
				padding: 4px;
			}

			QListWidget::item {
				min-height: 26px;
				padding: 4px 8px;
			}

			QListWidget::item:hover {
				background-color: #333333;
			}

			QListWidget::item:selected {
				background-color: #f0b000;
				color: #111111;
			}

			QPushButton {
				background-color: #4a4a4a;
				color: #ededed;
				border: none;
				border-radius: 3px;
				padding: 6px 10px;
				font-weight: 600;
				min-height: 26px;
			}

			QPushButton:hover {
				background-color: #5a5a5a;
			}

			QPushButton:pressed {
				background-color: #3a3a3a;
			}

			QPushButton#primaryButton {
				background-color: #f0b000;
				color: #111111;
			}

			QPushButton#primaryButton:hover {
				background-color: #ffc533;
			}

			QPushButton#primaryButton:pressed {
				background-color: #d89c00;
			}

			QPushButton#dangerButton {
				background-color: #5a2f2f;
				color: #ededed;
			}

			QPushButton#dangerButton:hover {
				background-color: #743838;
			}
		""")

		main_layout = QtWidgets.QVBoxLayout(self)
		main_layout.setContentsMargins(18, 16, 18, 16)
		main_layout.setSpacing(10)

		title = QtWidgets.QLabel(title_text.upper())
		title.setObjectName("dialogTitle")
		main_layout.addWidget(title)

		subtitle = QtWidgets.QLabel(subtitle_text)
		subtitle.setObjectName("dialogSubtitle")
		main_layout.addWidget(subtitle)

		self.list_widget = QtWidgets.QListWidget()
		self.list_widget.setEditTriggers(
			QtWidgets.QAbstractItemView.NoEditTriggers
		)

		for item_text in items:
			item = QtWidgets.QListWidgetItem(item_text)
			item.setFlags(item.flags() | QtCore.Qt.ItemIsEditable)
			self.list_widget.addItem(item)

		self.list_widget.itemDoubleClicked.connect(
			self.edit_wrangler_item
		)

		main_layout.addWidget(self.list_widget)

		action_row = QtWidgets.QHBoxLayout()
		action_row.setSpacing(8)

		self.btn_add = QtWidgets.QPushButton("Add")
		self.btn_delete = QtWidgets.QPushButton("Delete")
		self.btn_delete.setObjectName("dangerButton")

		action_row.addWidget(self.btn_add)
		action_row.addWidget(self.btn_delete)

		main_layout.addLayout(action_row)

		bottom_row = QtWidgets.QHBoxLayout()
		bottom_row.addStretch()

		self.btn_save = QtWidgets.QPushButton("Save Changes")
		self.btn_save.setObjectName("primaryButton")

		bottom_row.addWidget(self.btn_save)

		main_layout.addLayout(bottom_row)

		self.btn_add.clicked.connect(self.add_wrangler)
		self.btn_delete.clicked.connect(self.delete_wrangler)
		self.btn_save.clicked.connect(self.accept)

	def edit_wrangler_item(self, item):

		self.list_widget.editItem(item)

	def add_wrangler(self):

		text, ok = QtWidgets.QInputDialog.getText(
			self,
			self.add_dialog_title,
			self.add_dialog_label
		)

		if ok and text.strip():
			self.list_widget.addItem(text.strip())


	def delete_wrangler(self):
		item = self.list_widget.currentItem()

		if item:
			self.list_widget.takeItem(self.list_widget.row(item))

	def get_wranglers(self):
		return [
			self.list_widget.item(i).text()
			for i in range(self.list_widget.count())
		]

class LoadingDialog(QtWidgets.QDialog):

	def __init__(self, parent=None):
		super().__init__(parent)

		self.setWindowTitle("ShowTools")
		self.setModal(True)
		self.setFixedSize(380, 150)
		self.setWindowFlags(
			self.windowFlags() & ~QtCore.Qt.WindowContextHelpButtonHint
		)

		layout = QtWidgets.QVBoxLayout(self)
		layout.setContentsMargins(22, 18, 22, 18)
		layout.setSpacing(10)

		title = QtWidgets.QLabel("SHOWTOOLS")
		title.setObjectName("dialogTitle")
		layout.addWidget(title)

		message = QtWidgets.QLabel(
			"Sorting package...\nPlease wait while your data is being organised."
		)
		message.setWordWrap(True)
		layout.addWidget(message)

		self.progress_bar = QtWidgets.QProgressBar()
		self.progress_bar.setRange(0, 0)
		self.progress_bar.setTextVisible(False)
		layout.addWidget(self.progress_bar)

		self.setStyleSheet("""
			QDialog {
				background-color: #2f2f2f;
			}

			QLabel {
				background: transparent;
				color: #ededed;
			}

			QLabel#dialogTitle {
				color: #f0b000;
				font-size: 15pt;
				font-weight: 700;
			}

			QProgressBar {
				background-color: #1f1f1f;
				border: 1px solid #4a4a4a;
				border-radius: 3px;
				min-height: 18px;
			}

			QProgressBar::chunk {
				background-color: #4CAF50;
				border-radius: 2px;
			}
		""")


#ShowTools - Main App
class ShowTools:

	def __init__(self):
		self.wgShowTools = QtCompat.loadUi(str(UI_PATH))
		self.current_show_defaults_path = None
		self.ensure_user_app_folders()
		self.copy_bundled_config_if_missing()

		self.wgShowTools.input_wrangler.setView(QtWidgets.QListView())
		self.wgShowTools.input_unit.setView(QtWidgets.QListView())

		self.slate_element_count = 1

		import sys

		instructions_body = """
		<h3>PIPELINE PROFILE</h3>
		<p>Load YAML profiles that define how a package should be sorted, renamed, and processed. Profiles can be edited, reused, or created for specific tasks, shows, vendors, or pipeline requirements.</p>

		<h3>PROJECT DETAILS</h3>
		<p>Optional project, wrangler, and unit details used for tracking data and powering automated renaming tokens in the Rename Settings tab.</p>

		<h3>PACKAGE SETTINGS</h3>
		<p>Control what happens after sorting, such as tagging folders with suffixes like <b>_SORTED</b>, generating reports for ShotGrid or ftrack integration, notifying team members by email, and creating reversible sort data for later adjustments.</p>

		<h3>RENAME SETTINGS</h3>
		<p>This is where the main sorting logic is built. Create rules for specific data types such as HDRI, OVERVIEW, PANORAMA, TEXTURES, and more. ShowTools can build slate or asset folder structures, move items into the correct locations, and use metadata such as focal length for texture and photogrammetry datasets.</p>
		"""

		if sys.platform == "darwin":
			self.wgShowTools.txtInstructions.setHtml(f"""
			<html>
			<head>
			<style>

			body {{
				font-family: -apple-system, "SF Pro Text", "Helvetica Neue", Arial, sans-serif;
				font-size: 12px;
				line-height: 1.35;
				color: #dddddd;
			}}

			p {{
				margin-top: 0px;
				margin-bottom: 8px;
			}}

			h3 {{
				color: #f0b000;
				margin-top: 12px;
				margin-bottom: 4px;
				font-size: 14px;
				font-weight: 600;
			}}

			.welcome {{
				color: #ffffff;
				font-weight: 600;
				margin-bottom: 12px;
			}}

			.footer {{
				color: #ffffff;
				font-weight: 600;
				margin-top: 24px;
				margin-bottom: 8px;
			}}

			</style>
			</head>

			<body>

			<p class="welcome">
			Welcome to ShowTools!<br>
			Here's a quick overview of the application's core features.
			</p>

			{instructions_body}

			<p class="footer">
			Need more information?
			</p>

			<p>
			Feel free to explore the resources below for additional information about ShowTools.
			<br><br>
			If you'd like help configuring the tool for your studio or upcoming project,
			please don't hesitate to get in touch.
			</p>

			</body>
			</html>
			""")

		else:
			self.wgShowTools.txtInstructions.setHtml(f"""
			<html>
			<head>
			<style>

			body {{
				font-family: "Segoe UI", Arial, sans-serif;
				font-size: 10pt;
				line-height: 1.35;
				color: #dddddd;
			}}

			p {{
				margin-top: 0px;
				margin-bottom: 8px;
			}}

			h3 {{
				color: #f0b000;
				margin-top: 12px;
				margin-bottom: 4px;
				font-size: 11pt;
				font-weight: 700;
			}}

			.welcome {{
				color: #ffffff;
				font-weight: 600;
				margin-bottom: 12px;
			}}

			.footer {{
				color: #ffffff;
				font-weight: 600;
				margin-top: 24px;
				margin-bottom: 8px;
			}}

			</style>
			</head>

			<body>

			<p class="welcome">
			Welcome to ShowTools!<br>
			Here's a quick overview of the application's core features.
			</p>

			{instructions_body}

			<p class="footer">
			Need more information?
			</p>

			<p>
			Feel free to explore the resources below for additional information about ShowTools.
			<br><br>
			If you'd like help configuring the tool for your studio or upcoming project,
			please don't hesitate to get in touch.
			</p>

			</body>
			</html>
			""")


		# TABS
		self.wgShowTools.btn_mainSettings.clicked.connect(self.show_main_settings)
		self.wgShowTools.btn_renameSettings.clicked.connect(self.show_rename_settings)

		# WINDOW ICON
		self.wgShowTools.setWindowIcon(QtGui.QIcon(icon_path("showtools_icon_master_1024")))

		# LINK ICONS
		self.wgShowTools.btn_gmail.setIcon(QtGui.QIcon(icon_path("gmail_icon")))
		self.wgShowTools.btn_github.setIcon(QtGui.QIcon(icon_path("github_icon")))
		self.wgShowTools.btn_linkedin.setIcon(QtGui.QIcon(icon_path("linkedin_icon")))
		self.wgShowTools.btn_youtube.setIcon(QtGui.QIcon(icon_path("youtube_icon")))
		self.wgShowTools.btn_website.setIcon(QtGui.QIcon(icon_path("logo")))

		# TOOL ICONS
		self.wgShowTools.btn_browseConfig.setIcon(QtGui.QIcon(icon_path("browse_file_icon")))
		self.wgShowTools.btn_browseTargetFolder.setIcon(QtGui.QIcon(icon_path("browse_file_icon")))
		self.wgShowTools.btn_editWranglers.setIcon(QtGui.QIcon(icon_path("edit")))
		self.wgShowTools.btn_editUnits.setIcon(QtGui.QIcon(icon_path("edit")))
		self.wgShowTools.btn_editUnits.setText("")
		self.wgShowTools.btn_slateSettings.setIcon(QtGui.QIcon(icon_path("slate")))
		self.wgShowTools.btn_slateSettings.setText("")
		self.wgShowTools.btn_slateSettings.setIconSize(QtCore.QSize(16, 16))

		# SIGNALS
		# ------- MAIN SETINGS PAGE --------
		# ------- Action Buttons
		self.wgShowTools.btn_clearSettings.clicked.connect(self.press_clearSettings)
		self.wgShowTools.btn_browseConfig.clicked.connect(self.press_browseConfig)
		self.wgShowTools.btn_saveSettings.clicked.connect(self.press_saveSettings)
		self.wgShowTools.btn_browseTargetFolder.clicked.connect(self.press_browseTargetFolder)
		self.wgShowTools.input_targetFolder.textChanged.connect(self.update_revert_button_state)
		self.wgShowTools.btn_export.clicked.connect(self.press_export)
		self.wgShowTools.btn_showProfile.clicked.connect(self.show_profile_menu)
		self.wgShowTools.btn_slateSettings.clicked.connect(self.open_slate_settings)

		# ------- Links
		self.wgShowTools.btn_gmail.clicked.connect(self.press_loadGmail)
		self.wgShowTools.btn_github.clicked.connect(self.press_loadGithub)
		self.wgShowTools.btn_linkedin.clicked.connect(self.press_loadLinkedin)
		self.wgShowTools.btn_youtube.clicked.connect(self.press_loadYoutube)
		self.wgShowTools.btn_website.clicked.connect(self.press_loadWebsite)

		# ------- RENAME SETINGS PAGE --------
		# ------- Action Buttons
		self.wgShowTools.btn_addRule.clicked.connect(self.press_addRule)
		self.wgShowTools.btn_clearNamingRule.clicked.connect(self.press_clearNamingRule)
		self.wgShowTools.btn_revert.clicked.connect(self.press_revert)
		self.wgShowTools.btn_revert.setEnabled(False)
		self.wgShowTools.btn_editWranglers.clicked.connect(self.edit_wranglers)
		self.wgShowTools.btn_editUnits.clicked.connect(self.edit_units)
	
		# ------- RENAME TOKENS
		self.wgShowTools.btn_token_first.clicked.connect(self.press_btn_token_first)
		self.wgShowTools.btn_token_middle.clicked.connect(self.press_btn_token_middle)
		self.wgShowTools.btn_token_last.clicked.connect(self.press_btn_token_last)
		self.wgShowTools.btn_token_all.clicked.connect(self.press_btn_token_all)

		self.wgShowTools.btn_token_slate.clicked.connect(self.press_btn_token_slate)
		self.wgShowTools.btn_token_wrangler.clicked.connect(self.press_btn_token_wrangler)
		self.wgShowTools.btn_token_unit.clicked.connect(self.press_btn_token_unit)
		self.wgShowTools.btn_token_date.clicked.connect(self.press_btn_token_date)
		self.wgShowTools.btn_token_project.clicked.connect(self.press_btn_token_project)
		self.wgShowTools.btn_tokenShootDate.clicked.connect(self.press_btn_token_shoot_date)
		self.wgShowTools.btn_token_data_type.clicked.connect(self.press_btn_token_data_type)
		self.wgShowTools.btn_token_focal.clicked.connect(self.press_btn_token_focal)
		

		# ------- RULE SETTINGS SAVER
		self.wgShowTools.input_dataTypeRename.textChanged.connect(self.on_rule_editor_changed)
		self.wgShowTools.combo_sortBy.currentIndexChanged.connect(self.on_rule_editor_changed)
		self.wgShowTools.check_splitImageType.stateChanged.connect(self.on_rule_editor_changed)
		self.wgShowTools.check_deleteEmptyFolders.stateChanged.connect(self.on_rule_editor_changed)
		self.wgShowTools.input_namingRule.textChanged.connect(self.on_rule_editor_changed)

		# ------- SETUP --------

		self.wgShowTools.btn_linkedin.hide()
		self.wgShowTools.btn_youtube.hide()

		# ------- LIVE PREVIEW --------
		self.wgShowTools.input_targetFolder.textChanged.connect(self.update_live_preview)
		self.update_revert_button_state()
		self.setup_preview_model()

		self.wgShowTools.tree_preview.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAsNeeded)
		self.wgShowTools.tree_preview.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAsNeeded)
		self.wgShowTools.tree_preview.setRootIsDecorated(False)
		self.wgShowTools.tree_preview.setItemsExpandable(False)

		# RENAME RULES
		self.update_add_rule_button_state()
		self.rename_rules = []
		self.current_rule_index = None
		
		self.update_rules_list_height()
		self.wgShowTools.list_rules.currentRowChanged.connect(self.on_rule_selected)
		self.update_rule_editor_state()

		# Center dropdown items
		delegate = CenteredItemDelegate(self.wgShowTools.combo_sortBy)
		self.wgShowTools.combo_sortBy.setItemDelegate(delegate)

		# Center selected value
		combo = self.wgShowTools.combo_sortBy
		combo.setEditable(True)
		combo.lineEdit().setAlignment(QtCore.Qt.AlignCenter)
		combo.lineEdit().setReadOnly(True)

		# Shift text slightly right
		combo.lineEdit().setStyleSheet("""
			padding-left: 26px;
		""")

		#macOS style updater
		self.apply_macos_ui_fixes()

		# DATE
		self.wgShowTools.input_shootDate.setDate(QDate.currentDate())
		self.wgShowTools.input_shootDate.setDisplayFormat("yyyy-MM-dd")

		calendar = self.wgShowTools.input_shootDate.calendarWidget()
		calendar.setMinimumSize(360, 300)
		# PLACEHOLDER TEXT
		self.wgShowTools.input_configFile.setPlaceholderText("Select sorting template...")
		# TARGET FOLDER
		self.update_target_folder_state("")
		# SET TAB
		self.show_main_settings()
		# LOAD DEFAULTS
		if not self.load_startup_show_profile():
			self.load_show_defaults()

		# GET PATH FROM SYS.ARGV - RIGHT CLICK, SEND TO
		if len(sys.argv) > 1:
			startup_path = sys.argv[1]
			if os.path.isdir(startup_path):
				self.set_target_folder(startup_path)

		self.wgShowTools.show()

		self.wgShowTools.chk_renamePackage.stateChanged.connect(self.update_rename_fields_state)

		# SET INITIAL STATE
		self.update_rename_fields_state()

		# FIND PIPELINE PROFILES
		os.makedirs(PIPELINE_PROFILES_PATH, exist_ok=True)

	# ************************************************************************************************
	# TABS
	def show_main_settings(self):
		self.wgShowTools.stackedWidget.setCurrentIndex(0)
		self.update_tab_styles(active="main")

	def show_rename_settings(self):
		self.wgShowTools.stackedWidget.setCurrentIndex(1)
		self.update_tab_styles(active="rename")

	def update_tab_styles(self, active):
		active_style = """
			QPushButton {
				color: #d8a106;
				background: transparent;
				border: none;
			}
		"""

		inactive_style = """
			QPushButton {
				color: #f2f2f2;
				background: transparent;
				border: none;
			}

			QPushButton:hover {
				color: #d8a106;
			}
		"""

		if active == "main":
			self.wgShowTools.btn_mainSettings.setStyleSheet(active_style)
			self.wgShowTools.btn_renameSettings.setStyleSheet(inactive_style)

		elif active == "rename":
			self.wgShowTools.btn_mainSettings.setStyleSheet(inactive_style)
			self.wgShowTools.btn_renameSettings.setStyleSheet(active_style)

	# *********************************************************************#
	#HELPERS
	#REVERSE MANIFEST
	def edit_units(self):

		current_units = self.get_unit_options()

		dialog = WranglerDialog(
			current_units,
			title_text="Manage Units",
			subtitle_text="Add, rename, or remove units for this show profile.",
			add_dialog_title="Add Unit",
			add_dialog_label="Unit Name:",
			parent=self.wgShowTools
		)

		dialog.setWindowTitle("Manage Units")

		if dialog.exec():

			current_selection = self.wgShowTools.input_unit.currentText().strip()
			new_units = dialog.get_wranglers()

			self.wgShowTools.input_unit.clear()
			self.wgShowTools.input_unit.addItems(new_units)

			if current_selection in new_units:
				self.wgShowTools.input_unit.setCurrentText(current_selection)


	def get_unit_options(self):
		return [
			self.wgShowTools.input_unit.itemText(i).strip()
			for i in range(self.wgShowTools.input_unit.count())
			if self.wgShowTools.input_unit.itemText(i).strip()
		]

	def open_slate_settings(self):

		dialog = QtWidgets.QDialog(self.wgShowTools)
		dialog.setWindowTitle("Slate Settings")
		dialog.setModal(True)
		dialog.setFixedSize(360, 190)

		layout = QtWidgets.QVBoxLayout(dialog)
		layout.setContentsMargins(18, 16, 18, 16)
		layout.setSpacing(10)

		title = QtWidgets.QLabel("SLATE SETTINGS")
		title.setObjectName("dialogTitle")
		layout.addWidget(title)

		description = QtWidgets.QLabel(
			"Choose how many underscore-separated elements should be used to identify a slate."
		)
		description.setWordWrap(True)
		layout.addWidget(description)

		row = QtWidgets.QHBoxLayout()

		label = QtWidgets.QLabel("Slate Elements")
		spinbox = QtWidgets.QSpinBox()
		spinbox.setMinimum(1)
		spinbox.setMaximum(5)
		spinbox.setValue(self.slate_element_count)

		row.addWidget(label)
		row.addWidget(spinbox)

		layout.addLayout(row)

		example = QtWidgets.QLabel(
			"1 = 19A\n2 = 201_19A\n3 = 201_19A_MainUnit"
		)
		example.setObjectName("dialogSubtitle")
		layout.addWidget(example)

		button_row = QtWidgets.QHBoxLayout()
		button_row.addStretch()

		save_btn = QtWidgets.QPushButton("Save")
		save_btn.setObjectName("primaryButton")
		button_row.addWidget(save_btn)

		layout.addLayout(button_row)

		dialog.setStyleSheet("""
			QDialog {
				background-color: #2f2f2f;
			}

			QLabel {
				background: transparent;
				color: #ededed;
			}

			QLabel#dialogTitle {
				color: #f0b000;
				font-size: 15pt;
				font-weight: 700;
			}

			QLabel#dialogSubtitle {
				color: #bdbdbd;
				font-size: 9pt;
			}

			QSpinBox {
				background-color: #d6d6d6;
				color: #1b1b1b;
				border: 1px solid #bcbcbc;
				border-radius: 2px;
				padding: 2px 6px;
				min-height: 24px;
			}

			QSpinBox:focus {
				border: 1px solid #f0b000;
			}

			QPushButton {
				background-color: #4a4a4a;
				color: #ededed;
				border: none;
				border-radius: 3px;
				padding: 6px 10px;
				font-weight: 600;
				min-height: 26px;
			}

			QPushButton#primaryButton {
				background-color: #f0b000;
				color: #111111;
			}

			QPushButton#primaryButton:hover {
				background-color: #ffc533;
			}
		""")

		save_btn.clicked.connect(dialog.accept)

		if dialog.exec():
			self.slate_element_count = spinbox.value()

	def load_startup_show_profile(self):

		if not STARTUP_PROFILE_PATH.exists():
			return False

		try:
			with open(STARTUP_PROFILE_PATH, "r", encoding="utf-8") as yaml_file:
				data = yaml.safe_load(yaml_file) or {}

			profile_name = data.get("startup_profile", "").strip()

			if not profile_name:
				return False

			profile_path = SHOW_DEFAULTS_DIR / profile_name

			if not profile_path.exists():
				return False

			if self.load_show_defaults_file(str(profile_path)):
				self.current_show_defaults_path = str(profile_path)
				return True

			return False

		except Exception as error:
			print(f"Failed to load startup show profile: {error}")
			return False

	def press_setStartupDefault(self):

		if not self.current_show_defaults_path:
			self.show_message(
				"Startup Default Failed",
				"No Profile Selected",
				"Please load or save a show profile first."
			)
			return

		try:
			startup_data = {
				"startup_profile": os.path.basename(self.current_show_defaults_path)
			}

			with open(STARTUP_PROFILE_PATH, "w", encoding="utf-8") as yaml_file:
				yaml.dump(
					startup_data,
					yaml_file,
					default_flow_style=False,
					sort_keys=False
				)

			self.show_message(
				"Startup Default Set",
				"Profile Will Load On Startup",
				os.path.basename(self.current_show_defaults_path),
				str(STARTUP_PROFILE_PATH)
			)

		except Exception as error:
			self.show_message(
				"Startup Default Failed",
				"Could not set startup profile.",
				str(error)
			)

	def show_profile_menu(self):

		menu = QtWidgets.QMenu(self.wgShowTools)

		menu.setStyleSheet("""
			QMenu {
				background-color: #2f2f2f;
				color: #ededed;
				border: 1px solid #4a4a4a;
				padding: 4px;
			}

			QMenu::item {
				background-color: transparent;
				padding: 6px 24px 6px 12px;
				min-width: 160px;
			}

			QMenu::item:selected {
				background-color: #f0b000;
				color: #111111;
			}

			QMenu::separator {
				height: 1px;
				background-color: #5a5a5a;
				margin: 4px 8px;
			}
		""")

		load_action = menu.addAction("Load Profile...")
		save_action = menu.addAction("Save Profile As...")

		menu.addSeparator()

		default_action = menu.addAction(
			"Set As Startup Default"
		)

		selected_action = menu.exec(
			self.wgShowTools.btn_showProfile.mapToGlobal(
				self.wgShowTools.btn_showProfile.rect().bottomLeft()
			)
		)

		if selected_action == load_action:
			self.press_loadShowDefaults()

		elif selected_action == save_action:
			self.press_saveShowDefaults()

		elif selected_action == default_action:
			self.press_setStartupDefault()

	def load_show_defaults_file(self, file_path):
		try:
			with open(file_path, "r", encoding="utf-8") as f:
				data = yaml.safe_load(f) or {}

			project_defaults = data.get("project_defaults", {})
			unit_defaults = data.get("unit_defaults", {})
			wrangler_defaults = data.get("wrangler_defaults", {})

			project_name = project_defaults.get("project_name", "")
			self.wgShowTools.input_projectName.setText(project_name)

			# ---------- Units ----------
			units = unit_defaults.get("options", [])
			default_unit = unit_defaults.get("default_selection", "")

			# Backward compatibility with older profiles
			if not default_unit:
				default_unit = project_defaults.get("unit", "")

			if units:
				self.wgShowTools.input_unit.clear()
				self.wgShowTools.input_unit.addItems(units)

			if default_unit:
				idx = self.wgShowTools.input_unit.findText(
					default_unit,
					QtCore.Qt.MatchExactly
				)

				if idx >= 0:
					self.wgShowTools.input_unit.setCurrentIndex(idx)

			# ---------- Wranglers ----------
			wranglers = wrangler_defaults.get("options", [])
			default_wrangler = wrangler_defaults.get("default_selection", "")

			if wranglers:
				self.wgShowTools.input_wrangler.clear()
				self.wgShowTools.input_wrangler.addItems(wranglers)

			if default_wrangler:
				idx = self.wgShowTools.input_wrangler.findText(
					default_wrangler,
					QtCore.Qt.MatchExactly
				)

				if idx >= 0:
					self.wgShowTools.input_wrangler.setCurrentIndex(idx)

			return True

		except Exception as error:
			self.show_message(
				"Load Failed",
				"Could not load show defaults.",
				str(error)
			)
			return False

	def press_loadShowDefaults(self):
		file_path, _ = QFileDialog.getOpenFileName(
			self.wgShowTools,
			"Load Show Defaults",
			str(SHOW_DEFAULTS_DIR),
			"YAML Files (*.yaml *.yml);;All Files (*)"
		)

		if not file_path:
			return

		if self.load_show_defaults_file(file_path):
			self.show_message(
				"Load Successful",
				"Show Defaults Loaded",
				os.path.basename(file_path),
				file_path
			)
			self.current_show_defaults_path = file_path

	def press_saveShowDefaults(self):
		defaults_data = self.get_show_defaults_data()

		file_path, _ = QFileDialog.getSaveFileName(
			self.wgShowTools,
			"Save Show Defaults",
			str(SHOW_DEFAULTS_DIR),
			"YAML Files (*.yaml *.yml)"
		)

		if not file_path:
			return

		if not file_path.lower().endswith((".yaml", ".yml")):
			file_path += ".yaml"

		try:
			with open(file_path, "w", encoding="utf-8") as yaml_file:
				yaml.dump(
					defaults_data,
					yaml_file,
					default_flow_style=False,
					sort_keys=False
				)

			profile_name = os.path.basename(file_path)

			self.show_message(
				"Save Successful",
				"Show Defaults Saved",
				profile_name,
				file_path
			)

			self.current_show_defaults_path = file_path

		except Exception as error:
			self.show_message(
				"Save Failed",
				"Could not save show defaults.",
				str(error)
			)


	def get_wrangler_options(self):
		return [
			self.wgShowTools.input_wrangler.itemText(i).strip()
			for i in range(self.wgShowTools.input_wrangler.count())
			if self.wgShowTools.input_wrangler.itemText(i).strip()
		]

	def get_show_defaults_data(self):
		project_name = self.wgShowTools.input_projectName.text().strip()
		unit = self.wgShowTools.input_unit.currentText().strip()
		default_wrangler = self.wgShowTools.input_wrangler.currentText().strip()

		return {
			"show_profile": {
				"name": project_name or "Default Show",
				"auto_load_defaults": True,
				"apply_project_name_on_startup": True,
				"apply_wranglers_on_startup": True,
				"apply_email_defaults_on_startup": False,
			},
			"project_defaults": {
				"project_name": project_name,
				"unit": unit,
			},
			"unit_defaults": {
				"options": self.get_unit_options(),
				"default_selection": self.wgShowTools.input_unit.currentText().strip(),
			},
			"wrangler_defaults": {
				"options": self.get_wrangler_options(),
				"default_selection": default_wrangler,
			},
			"email_defaults": {
				"enabled_by_default": False,
				"subject": "{project_name} {clean_package_name} ready for ingestion",
				"body": (
					"Hi,\n\n"
					"{clean_package_name} is packaged and ready for ingestion.\n\n"
					"Thanks,\n"
				),
				"to": [],
				"cc": [],
			},
			"browser_defaults": {
				"preferred_browser": "default",
			},
		}

	def copy_bundled_config_if_missing(self):
		"""
		Copy bundled starter config files into the user-writable config folders.

		This only copies files that do not already exist, so user edits are not overwritten.
		"""
		copy_pairs = [
			(BUNDLED_PIPELINE_PROFILES_PATH, PIPELINE_PROFILES_PATH),
			(BUNDLED_SHOW_DEFAULTS_DIR, SHOW_DEFAULTS_DIR),
		]

		for source_dir, destination_dir in copy_pairs:
			if not source_dir.exists():
				continue

			destination_dir.mkdir(parents=True, exist_ok=True)

			for source_file in source_dir.iterdir():
				if not source_file.is_file():
					continue

				if source_file.suffix.lower() not in {".yaml", ".yml", ".json"}:
					continue

				destination_file = destination_dir / source_file.name

				if destination_file.exists():
					continue

				shutil.copy2(source_file, destination_file)

	def ensure_user_app_folders(self):
		USER_APP_DATA_DIR.mkdir(parents=True, exist_ok=True)
		PIPELINE_PROFILES_PATH.mkdir(parents=True, exist_ok=True)
		SHOW_DEFAULTS_DIR.mkdir(parents=True, exist_ok=True)

	def is_wildcard_data_type(self, value):
		return str(value).strip().lower() in {"*", "*all", "all"}

	def apply_macos_ui_fixes(self):
		import sys
		if sys.platform != "darwin":
			return

		# Remove visible frame around save/clear buttons container
		if hasattr(self.wgShowTools, "frame_settingsButtons"):
			self.wgShowTools.frame_settingsButtons.setStyleSheet("""
				QFrame#frame_settingsButtons {
					border: none;
					background-color: transparent;
				}
			""")

		# Slightly larger instruction text on macOS
		instruction_labels = [
			"label_instructionPipelineProfile",
			"label_instructionProjectDetails",
			"label_instructionPackageSettings",
		]

		for name in instruction_labels:
			if hasattr(self.wgShowTools, name):
				label = getattr(self.wgShowTools, name)
				font = label.font()
				font.setPointSize(font.pointSize() + 2)
				label.setFont(font)

	def get_revert_manifest_path(self, folder_path):
		if not folder_path:
			return None

		folder = Path(folder_path)
		return folder / ".showtools" / "revert_manifest.yaml"

	def validate_revert_manifest(self, manifest_path, folder_path):
		try:
			if not manifest_path or not manifest_path.is_file():
				return False

			with open(manifest_path, "r", encoding="utf-8") as f:
				data = yaml.safe_load(f) or {}

			manifest = data.get("export_manifest", {})
			if not manifest:
				return False

			manifest_root = manifest.get("manifest_root", "")
			if not manifest_root:
				return False

			selected = str(Path(folder_path).resolve())
			stored = str(Path(manifest_root).resolve())

			return selected == stored

		except Exception:
			return False

	def update_revert_button_state(self):
		folder_path = self.wgShowTools.input_targetFolder.text().strip()
		button = self.wgShowTools.btn_revert

		if not folder_path:
			button.setEnabled(False)
			button.setProperty("revertState", "disabled")
			button.style().unpolish(button)
			button.style().polish(button)
			return

		manifest_path = self.get_revert_manifest_path(folder_path)
		is_valid = self.validate_revert_manifest(manifest_path, folder_path)

		button.setEnabled(is_valid)

		if is_valid:
			button.setProperty("revertState", "ready")
		else:
			button.setProperty("revertState", "disabled")

		button.style().unpolish(button)
		button.style().polish(button)

	def write_revert_manifest(self, final_root, original_root, operations, output_root=None):
		try:
			manifest_dir = Path(final_root) / ".showtools"
			manifest_dir.mkdir(parents=True, exist_ok=True)

			manifest_path = manifest_dir / "revert_manifest.yaml"

			manifest_data = {
				"export_manifest": {
					"version": 1,
					"created_at": datetime.now().isoformat(timespec="seconds"),
					"original_root": str(Path(original_root).resolve()),
					"manifest_root": str(Path(final_root).resolve()),
					"output_root": str(Path(output_root or final_root).resolve()),
					"operations": operations,
				}
			}

			with open(manifest_path, "w", encoding="utf-8") as f:
				yaml.dump(manifest_data, f, default_flow_style=False, sort_keys=False)

			return manifest_path

		except Exception as error:
			print(f"Failed to write revert manifest: {error}")
			return None

	def read_revert_manifest(self, folder_path):
		manifest_path = self.get_revert_manifest_path(folder_path)
		if not manifest_path or not manifest_path.is_file():
			return None

		try:
			with open(manifest_path, "r", encoding="utf-8") as f:
				return yaml.safe_load(f) or {}
		except Exception:
			return None

	def confirm_revert_sort(self):
		dialog = ConfirmActionDialog(
			title="Revert Sort",
			heading="Revert This Package?",
			detail="This will restore the folder structure and names to their original state.",
			sub_detail="Any changes made after sorting may be lost or cannot be fully restored.",
			confirm_text="Revert",
			parent=self.wgShowTools
		)
		return dialog.exec() == QtWidgets.QDialog.Accepted

	def get_manifest_operations(self, folder_path):
		data = self.read_revert_manifest(folder_path)
		if not data:
			return []

		manifest = data.get("export_manifest", {})
		return manifest.get("operations", [])

	def reverse_single_operation(self, operation):
		op_type = operation.get("type", "").strip()

		if op_type in {"move", "rename_folder", "rename_package"}:
			src = operation.get("from", "")
			dst = operation.get("to", "")

			if not src or not dst:
				return False, f"Missing paths for operation '{op_type}'"

			if not os.path.exists(dst):
				return False, f"Expected current path does not exist: {dst}"

			parent = os.path.dirname(src)
			if parent and not os.path.exists(parent):
				os.makedirs(parent, exist_ok=True)

			if os.path.exists(src):
				return False, f"Original path already exists, cannot restore: {src}"

			os.rename(dst, src)
			return True, f"Restored {dst} -> {src}"

		elif op_type == "split":
			folder = operation.get("folder", "")

			if not folder or not os.path.isdir(folder):
				return False, f"Split folder missing: {folder}"

			subfolders = [
				os.path.join(folder, name)
				for name in os.listdir(folder)
				if os.path.isdir(os.path.join(folder, name))
			]

			for subfolder in subfolders:
				for name in os.listdir(subfolder):
					src_file = os.path.join(subfolder, name)
					dst_file = os.path.join(folder, name)

					if not os.path.isfile(src_file):
						continue

					if os.path.exists(dst_file):
						return False, f"Cannot unsplit because file already exists: {dst_file}"

					shutil.move(src_file, dst_file)

				if os.path.isdir(subfolder) and not os.listdir(subfolder):
					os.rmdir(subfolder)

			return True, f"Unsplit files back into: {folder}"

		return False, f"Unsupported operation type: {op_type}"

	def revert_operations_from_manifest(self, folder_path):
		operations = self.get_manifest_operations(folder_path)

		if not operations:
			return {
				"success": False,
				"messages": ["No operations found in revert manifest."],
			}

		results = []
		all_success = True

		for index, operation in enumerate(reversed(operations), start=1):
			op_type = operation.get("type", "unknown")

			try:
				ok, message = self.reverse_single_operation(operation)
				results.append(f"[{index}] {op_type}: {message}")

				if not ok:
					all_success = False
					results.append(f"    Operation data: {operation}")

			except Exception as error:
				all_success = False
				results.append(f"[{index}] {op_type}: ERROR - {error}")
				results.append(f"    Operation data: {operation}")

		return {
			"success": all_success,
			"messages": results,
		}

	def remove_empty_dir_tree(self, path):
		path = Path(path)

		if not path.exists() or not path.is_dir():
			return

		for child in list(path.iterdir()):
			if child.is_dir():
				self.remove_empty_dir_tree(child)

		if not any(path.iterdir()):
			path.rmdir()

	def write_revert_debug_log(self, folder_path, messages):
		try:
			log_dir = Path(folder_path) / ".showtools"
			log_dir.mkdir(parents=True, exist_ok=True)

			log_path = log_dir / "revert_debug_log.txt"

			with open(log_path, "w", encoding="utf-8") as f:
				for line in messages:
					f.write(str(line) + "\n")

			return log_path
		except Exception as error:
			print(f"Failed to write revert debug log: {error}")
			return None

	#PIPELINE PROFILE
	def get_pipeline_profile_data(self):
		self.save_current_rule_settings()

		return {
			"project_details": {
				"project_name": self.wgShowTools.input_projectName.text().strip(),
			},
			"package_settings": {
				"rename_package": self.wgShowTools.chk_renamePackage.isChecked(),
				"remove": self.wgShowTools.input_remove.text().strip(),
				"prefix": self.wgShowTools.input_prefix.text().strip(),
				"suffix": self.wgShowTools.input_suffix.text().strip(),
				"generate_yaml": self.wgShowTools.chk_generateYAML.isChecked(),
				"notify_by_email": self.wgShowTools.chk_notifyByEmail.isChecked(),
				"create_revert_manifest": self.wgShowTools.chk_reverseManifest.isChecked(),
				"slate_element_count": self.slate_element_count,
			},
			"rename_rules": self.rename_rules,
		}

	def load_rename_rules_from_profile(self, rename_rules):
		"""
		Replace current rename rules with those loaded from a profile
		and rebuild the rules list UI.
		"""
		self.save_current_rule_settings()

		list_widget = self.wgShowTools.list_rules
		list_widget.blockSignals(True)

		list_widget.clear()
		self.rename_rules = []
		self.current_rule_index = None

		for i, rule in enumerate(rename_rules):
			rule_data = {
				"name": rule.get("name", f"CONVENTION {i + 1}"),
				"data_type": rule.get("data_type", ""),
				"sort_by": rule.get("sort_by", ""),
				"split_image_type": rule.get("split_image_type", False),
				"delete_empty_folders": rule.get("delete_empty_folders", False),
				"naming_rule": rule.get("naming_rule", "{ALL}"),
			}

			self.rename_rules.append(rule_data)

			item = QtWidgets.QListWidgetItem()
			item.setSizeHint(QtCore.QSize(0, 44))

			display_name = rule_data["data_type"].strip() or rule_data["name"]
			widget = RuleListItemWidget(display_name)

			list_widget.addItem(item)
			list_widget.setItemWidget(item, widget)

			widget.btn_delete.clicked.connect(lambda _, it=item: self.delete_rule_item(it))

		list_widget.blockSignals(False)

		# Refresh list/editor UI state
		self.update_rules_list_height()
		self.update_add_rule_button_state()
		self.update_rule_editor_state()
		self.refresh_rule_item_selection_ui()
		self.update_live_preview()

		if self.rename_rules:
			list_widget.setCurrentRow(0)
		else:
			self.current_rule_index = None
		
	#FOCAL LENGTH DETECTORS
	def detect_folder_focal_length(self, folder_path):
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
			

			focal_value = self.extract_focal_length_from_image(file_path)
			if focal_value:
				return focal_value

		return ""

	def extract_focal_length_from_image(self, image_path):
		"""
		Read focal length metadata and return it as a string like '35mm'.
		Returns '' if unavailable.
		"""
		try:
			with Image.open(image_path) as img:
				exif = img.getexif()			

				if not exif:
					return ""

				focal_raw = None

				# 1) Try the merged/top-level EXIF first
				focal_raw = exif.get(ExifTags.Base.FocalLength)

				# 2) If not there, try the EXIF IFD explicitly
				if focal_raw is None:
					try:
						exif_ifd = exif.get_ifd(ExifTags.IFD.Exif)
						focal_raw = exif_ifd.get(ExifTags.Base.FocalLength)
					except Exception:
						pass

				# 3) Optional fallback: 35mm-equivalent if true focal isn't present
				if focal_raw is None:
					try:
						exif_ifd = exif.get_ifd(ExifTags.IFD.Exif)
						focal_raw = exif_ifd.get(ExifTags.Base.FocalLengthIn35mmFilm)
					except Exception:
						pass

				if focal_raw is None:
					return ""


				focal_clean = self.format_focal_length_value(focal_raw)
				if not focal_clean:
					return ""

				return f"{focal_clean}mm"

		except Exception as error:
			return ""

	def format_focal_length_value(self, focal_raw):
		"""
		Convert EXIF values like 35, 35.0, or rational values into '35' or '35.5'.
		"""
		try:
			# tuple-like rational
			if isinstance(focal_raw, tuple) and len(focal_raw) == 2:
				num, den = focal_raw
				if den == 0:
					return ""
				value = float(num) / float(den)
			else:
				# handles int, float, and Pillow's rational-like values
				value = float(focal_raw)

			if value.is_integer():
				return str(int(value))

			return f"{value:.1f}".rstrip("0").rstrip(".")
		except Exception:
			return ""

	#RULE ITEMS
	def confirm_delete_rule(self, rule_name):
		dialog = ConfirmActionDialog(
			title="Delete Rule",
			heading="Delete Naming Convention?",
			detail=f'Are you sure you want to delete "{rule_name}"?',
			sub_detail="This action cannot be undone.",
			parent=self.wgShowTools
		)
		return dialog.exec() == QtWidgets.QDialog.Accepted	

	def refresh_rule_item_selection_ui(self):
		"""Show delete button only on selected row and update text color."""
		for i in range(self.wgShowTools.list_rules.count()):
			item = self.wgShowTools.list_rules.item(i)
			if not item:
				continue

			widget = self.wgShowTools.list_rules.itemWidget(item)
			if widget:
				widget.set_selected(i == self.current_rule_index)

	def update_add_rule_button_state(self):
		"""Make Add Rule look like a primary item only when no rules exist."""
		has_no_rules = self.wgShowTools.list_rules.count() == 0

		self.wgShowTools.btn_addRule.setProperty("emptyState", has_no_rules)
		self.wgShowTools.btn_addRule.style().unpolish(self.wgShowTools.btn_addRule)
		self.wgShowTools.btn_addRule.style().polish(self.wgShowTools.btn_addRule)

	def setup_preview_model(self):
		"""Create the model used by the live preview tree."""
		self.preview_model = QStandardItemModel()
		self.preview_model.setColumnCount(1)
		self.preview_model.setHeaderData(0, QtCore.Qt.Horizontal, "Output Name")

		self.wgShowTools.tree_preview.setModel(self.preview_model)

		# Tree behaviour
		self.wgShowTools.tree_preview.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
		self.wgShowTools.tree_preview.setSelectionMode(QtWidgets.QAbstractItemView.SingleSelection)
		self.wgShowTools.tree_preview.setRootIsDecorated(False)
		self.wgShowTools.tree_preview.setItemsExpandable(False)
		self.wgShowTools.tree_preview.setAllColumnsShowFocus(True)

		# Scrolling / display
		self.wgShowTools.tree_preview.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAsNeeded)
		self.wgShowTools.tree_preview.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAsNeeded)
		self.wgShowTools.tree_preview.setHorizontalScrollMode(QtWidgets.QAbstractItemView.ScrollPerPixel)
		self.wgShowTools.tree_preview.setTextElideMode(QtCore.Qt.ElideNone)
		self.wgShowTools.tree_preview.setAlternatingRowColors(False)

		# Column sizing
		header = self.wgShowTools.tree_preview.header()
		header.hide()
		header.setStretchLastSection(True)
		header.setSectionResizeMode(0, QtWidgets.QHeaderView.Stretch)

	def update_data_type_field_state(self, state="neutral"):
		"""
		Update the Data Type field visual state.

		state:
			- "neutral"
			- "valid"
			- "missing"
		"""
		widget = self.wgShowTools.input_dataTypeRename
		widget.setProperty("dataTypeState", state)
		widget.style().unpolish(widget)
		widget.style().polish(widget)

	def get_current_rule_source_folders(self):
		"""
		Return matched source folders for the currently selected rule.

		Supports:
		1. target_folder / data_type
		2. target_folder itself if its name matches data_type
		3. wildcard data type: *, *all, all
		"""
		if self.current_rule_index is None:
			return []

		target_folder_text = self.wgShowTools.input_targetFolder.text().strip()
		data_type_text = self.wgShowTools.input_dataTypeRename.text().strip()

		if not target_folder_text or not data_type_text:
			return []

		target_folder = Path(target_folder_text)
		if not target_folder.is_dir():
			return []

		if self.is_wildcard_data_type(data_type_text):
			return sorted(
				[child for child in target_folder.iterdir() if child.is_dir()],
				key=lambda p: p.name.lower()
			)

		candidate = target_folder / data_type_text
		if candidate.is_dir():
			return [candidate]

		if target_folder.name.lower() == data_type_text.lower():
			return [target_folder]

		return []

	def get_preview_folder_names(self, source_folder):
		"""Return immediate child folder names from the matched data-type folder."""
		if not source_folder or not source_folder.is_dir():
			return []

		folder_names = []
		for child in source_folder.iterdir():
			if child.is_dir():
				folder_names.append(child.name)

		return sorted(folder_names, key=str.lower)

	def parse_name_segments(self, original_name):
		"""Split an original folder name into underscore-separated segments."""
		if not original_name:
			return []

		return [segment for segment in original_name.split("_") if segment]

	def build_preview_name(self, original_name, rule):
		"""
		Apply the current naming rule to a folder name.

		Supported name tokens:
			{ALL}
			{FIRST}
			{MIDDLE}
			{LAST}

		Supported metadata tokens:
			{SLATE}
			{WRANGLER}
			{UNIT}
			{DATE}
			{PROJECT}
			{SHOOT_DATE}
			{DATA_TYPE}
			{FOCAL}
		"""
		naming_rule = rule.get("naming_rule", "").strip()
		if not naming_rule:
			naming_rule = "{ALL}"

		segments = self.parse_name_segments(original_name)

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

		focal_value = rule.get("focal", "").strip()
		if not focal_value:
			focal_value = "VARIABLEmm"

		replacements = {
			"{ALL}": all_name,
			"{FIRST}": first,
			"{REST}": rest,
			"{LAST}": last,
			"{SLATE}": self.wgShowTools.input_wrangler.currentText().strip() if False else first,
			"{WRANGLER}": self.wgShowTools.input_wrangler.currentText().strip(),
			"{UNIT}": self.wgShowTools.input_unit.currentText().strip(),
			"{DATE}": datetime.now().strftime("%Y%m%d"),
			"{PROJECT}": self.wgShowTools.input_projectName.text().strip(),
			"{SHOOT_DATE}": self.wgShowTools.input_shootDate.date().toString("yyyyMMdd"),
			"{DATA_TYPE}": rule.get("data_type", "").strip(),
			"{FOCAL}": focal_value,
		}

		preview_name = naming_rule

		for token, value in replacements.items():
			preview_name = preview_name.replace(token, value)

		# Cleanup repeated underscores from missing values
		while "__" in preview_name:
			preview_name = preview_name.replace("__", "_")

		preview_name = preview_name.strip("_")
		return preview_name

	def set_preview_empty_state(self, detail_text="Preview will appear here."):
		
		if hasattr(self.wgShowTools, "label_previewEmptyDetail"):
			self.wgShowTools.label_previewEmptyDetail.setText(detail_text)

		if hasattr(self.wgShowTools, "stackedWidget_preview"):
			if hasattr(self.wgShowTools, "page_previewEmpty"):
				self.wgShowTools.stackedWidget_preview.setCurrentWidget(self.wgShowTools.page_previewEmpty)

	def set_preview_tree_state(self):
		
		if hasattr(self.wgShowTools, "stackedWidget_preview"):
			if hasattr(self.wgShowTools, "page_previewTree"):
				self.wgShowTools.stackedWidget_preview.setCurrentWidget(self.wgShowTools.page_previewTree)

	def update_live_preview(self):
		"""Refresh data-type validation and the live folder preview."""
		self.preview_model.removeRows(0, self.preview_model.rowCount())

		# No rule selected
		if self.current_rule_index is None or self.current_rule_index >= len(self.rename_rules):
			self.update_data_type_field_state("neutral")
			self.set_preview_empty_state("Add a rule to begin previewing.")
			return

		rule = self.rename_rules[self.current_rule_index]
		source_folders = self.get_current_rule_source_folders()
		data_type_text = self.wgShowTools.input_dataTypeRename.text().strip()

		# No data type entered yet
		if not data_type_text:
			self.update_data_type_field_state("neutral")
			self.set_preview_empty_state("Enter a Data Type to preview folders.")
			return

		# No valid matching folder
		if not source_folders:
			self.update_data_type_field_state("missing")
			self.set_preview_empty_state(f'No "{data_type_text}" folder found in target folder.')
			return

		self.update_data_type_field_state("valid")

		any_items_found = False

		for source_folder in source_folders:
			folder_names = self.get_preview_folder_names(source_folder)

			for folder_name in folder_names:
				any_items_found = True

				folder_path = source_folder / folder_name

				preview_rule = rule.copy()
				preview_rule["data_type"] = source_folder.name
				preview_rule["focal"] = self.detect_folder_focal_length(str(folder_path))

				preview_name = self.build_preview_name(folder_name, preview_rule)

				preview_item = QStandardItem(preview_name)
				preview_item.setEditable(False)
				preview_item.setToolTip(preview_name)

				self.preview_model.appendRow([preview_item])

		if not any_items_found:
			self.set_preview_empty_state("No previewable folders found.")
			return

		self.set_preview_tree_state()
		self.wgShowTools.tree_preview.expandAll()

	#RULES HEIGHT
	def update_rules_list_height(self):
		"""Resize the rules list so Add Rule sits under the last item, up to a max height."""
		list_widget = self.wgShowTools.list_rules
		count = list_widget.count()

		if count == 0:
			list_widget.setFixedHeight(0)
			return

		row_height = list_widget.sizeHintForRow(0)
		frame = list_widget.frameWidth() * 2
		padding = 2

		total_height = (row_height * count) + frame + padding

		# Max visible rows before scrollbar takes over
		max_visible_rows = 11
		max_height = (row_height * max_visible_rows) + frame + padding

		list_widget.setFixedHeight(min(total_height, max_height))

	#RULES SETTINGS
	def on_rule_selected(self, row):
		"""Save the current rule, then load the newly selected rule."""
		if row < 0 or row >= len(self.rename_rules):
			self.current_rule_index = None
			self.update_rule_editor_state()
			self.update_live_preview()
			return

		# Save the rule that was previously selected
		if self.current_rule_index is not None and self.current_rule_index < len(self.rename_rules):
			self.save_current_rule_settings()

		self.current_rule_index = row
		self.load_rule_settings(row)
		self.update_rule_editor_state()
		self.update_live_preview()
		self.refresh_rule_item_selection_ui()
	
	def save_current_rule_settings(self):
		"""Save the current editor values into the selected rule."""
		if self.current_rule_index is None:
			return

		rule = self.rename_rules[self.current_rule_index]

		rule["data_type"] = self.wgShowTools.input_dataTypeRename.text().strip()
		rule["sort_by"] = self.wgShowTools.combo_sortBy.currentText().strip()
		rule["split_image_type"] = self.wgShowTools.check_splitImageType.isChecked()
		rule["delete_empty_folders"] = self.wgShowTools.check_deleteEmptyFolders.isChecked()
		rule["naming_rule"] = self.wgShowTools.input_namingRule.text().strip()

		self.update_rule_display_name(self.current_rule_index)
	
	def load_rule_settings(self, index):
		"""Load a rule's saved settings into the editor."""
		if index < 0 or index >= len(self.rename_rules):
			return

		rule = self.rename_rules[index]

		widgets = [
			self.wgShowTools.input_dataTypeRename,
			self.wgShowTools.combo_sortBy,
			self.wgShowTools.check_splitImageType,
			self.wgShowTools.check_deleteEmptyFolders,
			self.wgShowTools.input_namingRule,
		]

		for widget in widgets:
			widget.blockSignals(True)

		self.wgShowTools.input_dataTypeRename.setText(rule.get("data_type", ""))

		sort_by_index = self.wgShowTools.combo_sortBy.findText(
			rule.get("sort_by", ""),
			QtCore.Qt.MatchExactly
		)
		if sort_by_index >= 0:
			self.wgShowTools.combo_sortBy.setCurrentIndex(sort_by_index)
		else:
			self.wgShowTools.combo_sortBy.setCurrentIndex(0)

		self.wgShowTools.check_splitImageType.setChecked(rule.get("split_image_type", False))
		self.wgShowTools.check_deleteEmptyFolders.setChecked(rule.get("delete_empty_folders", False))
		self.wgShowTools.input_namingRule.setText(rule.get("naming_rule", ""))

		for widget in widgets:
			widget.blockSignals(False)

	def update_rule_display_name(self, index):
		"""Update the outliner item name based on the rule data."""
		if index < 0 or index >= len(self.rename_rules):
			return

		rule = self.rename_rules[index]

		if rule.get("data_type", "").strip():
			display_name = rule["data_type"].strip()
		else:
			display_name = f"CONVENTION {index + 1}"

		rule["name"] = display_name

		item = self.wgShowTools.list_rules.item(index)
		if not item:
			return

		widget = self.wgShowTools.list_rules.itemWidget(item)
		if widget:
			widget.set_text(display_name)

	def on_rule_editor_changed(self):
		"""Live-save editor changes into the currently selected rule."""
		if self.current_rule_index is None:
			return

		self.save_current_rule_settings()
		self.update_live_preview()

	def update_rule_editor_state(self):
		"""Show placeholder page when no rule is selected, otherwise show the editor page."""
		has_selection = (
			self.current_rule_index is not None
			and 0 <= self.current_rule_index < len(self.rename_rules)
		)

		if has_selection:
			self.wgShowTools.stackedWidget_ruleEditor.setCurrentWidget(self.wgShowTools.page_ruleEditor)
		else:
			self.wgShowTools.stackedWidget_ruleEditor.setCurrentWidget(self.wgShowTools.page_noRules)

	#TOKEN RENAMING
	def insert_naming_token(self, token_text):
		"""Insert a naming token into the naming rule input, adding underscores only when needed."""
		line_edit = self.wgShowTools.input_namingRule
		line_edit.setFocus()

		text = line_edit.text()
		cursor_pos = line_edit.cursorPosition()
		selected_text = line_edit.selectedText()

		# If user has selected text, replace it directly with the token
		if selected_text:
			line_edit.insert(token_text)
			return

		before = text[:cursor_pos]
		after = text[cursor_pos:]

		insert_text = token_text

		# Add underscore before token if needed
		if before and not before.endswith("_"):
			insert_text = "_" + insert_text

		# Add underscore after token if needed
		if after and not after.startswith("_"):
			insert_text = insert_text + "_"

		line_edit.insert(insert_text)

	#LINKS
	def open_link(self, url):
		preferred_browser = "default"

		if hasattr(self, "browser_defaults"):
			preferred_browser = self.browser_defaults.get("preferred_browser", "default").lower()

		browser_map = {
			"chrome": [
				"C:/Program Files/Google/Chrome/Application/chrome.exe %s",
				"C:/Program Files (x86)/Google/Chrome/Application/chrome.exe %s",
			],
			"edge": [
				"C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe %s",
				"C:/Program Files/Microsoft/Edge/Application/msedge.exe %s",
			],
		}

		if preferred_browser in browser_map:
			for browser_path in browser_map[preferred_browser]:
				if os.path.exists(browser_path.replace(" %s", "")):
					try:
						webbrowser.get(browser_path).open(url)
						return
					except Exception:
						pass

		webbrowser.open(url)

	def open_email_client(self, subject, body, to_list=None, cc_list=None):
		to = ",".join(to_list or [])
		cc = ",".join(cc_list or [])

		preferred_browser = "default"

		if hasattr(self, "browser_defaults"):
			preferred_browser = self.browser_defaults.get("preferred_browser", "default").lower()

		# CASE 1: Use system default email client (mailto)
		if preferred_browser == "default":
			params = {
				"subject": subject,
				"body": body
			}

			if cc:
				params["cc"] = cc

			query = urllib.parse.urlencode(params, quote_via=urllib.parse.quote)
			url = f"mailto:{to}?{query}"

			webbrowser.open(url)
			return

		# CASE 2: Use Gmail in browser
		params = {
			"view": "cm",
			"to": to,
			"su": subject,
			"body": body
		}

		if cc:
			params["cc"] = cc

		query = urllib.parse.urlencode(params, quote_via=urllib.parse.quote)
		url = f"https://mail.google.com/mail/?{query}"

		self.open_link(url)

	def format_email_text(self, text, context):
		if not text:
			return ""

		try:
			return text.format(**context)
		except Exception:
			return text

	def load_show_defaults(self):
		data = {}
		defaults_path = SHOW_DEFAULTS_DIR / SELECTED_DEFAULT_SETTINGS

		if not defaults_path.exists():
			return

		try:
			with open(defaults_path, "r", encoding="utf-8") as f:
				data = yaml.safe_load(f) or {}

			show_profile = data.get("show_profile", {})
			project_defaults = data.get("project_defaults", {})
			wrangler_defaults = data.get("wrangler_defaults", {})
			email_defaults = data.get("email_defaults", {})

			# Master toggle
			if not show_profile.get("auto_load_defaults", False):
				return

			# Project Defaults
			if show_profile.get("apply_project_name_on_startup", True):
				if not self.wgShowTools.input_projectName.text().strip():
					self.wgShowTools.input_projectName.setText(
						project_defaults.get("project_name", "")
					)

			if project_defaults.get("unit"):
				unit = project_defaults.get("unit")
				idx = self.wgShowTools.input_unit.findText(unit, QtCore.Qt.MatchExactly)
				if idx >= 0:
					self.wgShowTools.input_unit.setCurrentIndex(idx)

			# Wrangler Defaults
			if show_profile.get("apply_wranglers_on_startup", True):
				wranglers = wrangler_defaults.get("options", [])

				if wranglers:
					self.wgShowTools.input_wrangler.clear()
					self.wgShowTools.input_wrangler.addItems(wranglers)

					default_wrangler = wrangler_defaults.get("default_selection", "")
					idx = self.wgShowTools.input_wrangler.findText(
						default_wrangler, QtCore.Qt.MatchExactly
					)
					if idx >= 0:
						self.wgShowTools.input_wrangler.setCurrentIndex(idx)

			# Email Defaults
			if show_profile.get("apply_email_defaults_on_startup", False):
				enabled = email_defaults.get("enabled_by_default", False)
				self.wgShowTools.chk_notifyByEmail.setChecked(enabled)

			self.email_defaults = email_defaults

		except Exception as error:
			print(f"Failed to load show defaults: {error}")

		self.browser_defaults = data.get("browser_defaults", {})

	def update_rename_fields_state(self):
		enabled = self.wgShowTools.chk_renamePackage.isChecked()

		# Inputs
		self.wgShowTools.input_remove.setEnabled(enabled)
		self.wgShowTools.input_prefix.setEnabled(enabled)
		self.wgShowTools.input_suffix.setEnabled(enabled)

		# Labels
		active_color = "#ffffff"
		disabled_color = "#7a7a7a"

		color = active_color if enabled else disabled_color

		self.wgShowTools.label_remove.setStyleSheet(f"color: {color};")
		self.wgShowTools.label_prefix.setStyleSheet(f"color: {color};")
		self.wgShowTools.label_suffix.setStyleSheet(f"color: {color};")

		if not enabled:
			self.wgShowTools.input_remove.clear()
			self.wgShowTools.input_prefix.clear()
			self.wgShowTools.input_suffix.clear()

	def update_target_folder_state(self, folder_path=""):
		if folder_path and os.path.isdir(folder_path):
			state = "valid"
		else:
			state = "missing"

		widget = self.wgShowTools.input_targetFolder
		widget.setProperty("pathState", state)
		widget.style().unpolish(widget)
		widget.style().polish(widget)

	def set_target_folder(self, folder_path):
		self.wgShowTools.input_targetFolder.setText(folder_path if folder_path else "")
		self.wgShowTools.input_targetFolder.setToolTip(folder_path if folder_path else "")
		self.update_target_folder_state(folder_path)

	def confirm_empty_folders(self, empty_folders):
		dialog = EmptyFoldersDialog(empty_folders, parent=self.wgShowTools)
		return dialog.exec() == QtWidgets.QDialog.Accepted

	def show_message(self, title, heading, detail="", sub_detail=""):
		dialog = CustomMessageDialog(
			title=title,
			heading=heading,
			detail=detail,
			sub_detail=sub_detail,
			parent=self.wgShowTools
		)
		dialog.exec()

	def get_settings_data(self):
		return {
			"project_details": {
				"project_name": self.wgShowTools.input_projectName.text().strip(),
				"shoot_date": self.wgShowTools.input_shootDate.date().toString("yyyy-MM-dd"),
				"wrangler": self.wgShowTools.input_wrangler.currentText().strip(),
				"unit": self.wgShowTools.input_unit.currentText().strip(),
			},
			"package_settings": {
				"rename_package": self.wgShowTools.chk_renamePackage.isChecked(),
				"remove": self.wgShowTools.input_remove.text().strip(),
				"prefix": self.wgShowTools.input_prefix.text().strip(),
				"suffix": self.wgShowTools.input_suffix.text().strip(),
				"generate_yaml": self.wgShowTools.chk_generateYAML.isChecked(),
				"notify_by_email": self.wgShowTools.chk_notifyByEmail.isChecked(),
				"create_revert_manifest": self.wgShowTools.chk_reverseManifest.isChecked(),
			},
			"rename_rules": self.rename_rules,
		}

	def load_settings_from_yaml(self, file_path):
		try:
			with open(file_path, "r", encoding="utf-8") as yaml_file:
				settings_data = yaml.safe_load(yaml_file) or {}

			project_details = settings_data.get("project_details", {})
			package_settings = settings_data.get("package_settings", {})
			rename_rules = settings_data.get("rename_rules", [])

			# ------------------------------------------------
			# Project Details
			# Only apply project name from the profile
			# ------------------------------------------------
			project_name = project_details.get("project_name", None)
			if project_name is not None:
				self.wgShowTools.input_projectName.setText(project_name)

			# ------------------------------------------------
			# Package Settings
			# ------------------------------------------------
			self.wgShowTools.chk_renamePackage.setChecked(
				package_settings.get("rename_package", False)
			)
			self.wgShowTools.input_remove.setText(package_settings.get("remove", ""))
			self.wgShowTools.input_prefix.setText(package_settings.get("prefix", ""))
			self.wgShowTools.input_suffix.setText(package_settings.get("suffix", ""))
			self.wgShowTools.chk_generateYAML.setChecked(
				package_settings.get("generate_yaml", False)
			)
			self.wgShowTools.chk_notifyByEmail.setChecked(
				package_settings.get("notify_by_email", False)
			)
			self.wgShowTools.chk_reverseManifest.setChecked(
				package_settings.get("create_revert_manifest", True)
			)
			self.slate_element_count = int(
				package_settings.get("slate_element_count", 1)
			)

			self.wgShowTools.btn_slateSettings.setToolTip(
				f"Slate Settings\n\nCurrent slate elements: {self.slate_element_count}"
			)

			# ------------------------------------------------
			# Rename Rules
			# ------------------------------------------------
			self.load_rename_rules_from_profile(rename_rules)

			self.wgShowTools.input_configFile.setText(file_path)

			profile_name = os.path.basename(file_path)

			self.show_message(
				"Load Successful",
				"Loaded Profile",
				profile_name
			)

		except Exception as error:
			self.show_message(
				"Load Failed",
				"Could not load settings.",
				str(error)
			)

	# *********************************************************************#
	# PRESS - MAIN SETTINGS PAGE
	def press_clearSettings(self):
		self.wgShowTools.input_configFile.clear()
		self.wgShowTools.input_configFile.setPlaceholderText("Select sorting template...")

		self.wgShowTools.input_projectName.setText("")
		self.wgShowTools.input_wrangler.setCurrentIndex(0)
		self.wgShowTools.input_unit.setCurrentIndex(0)
		self.wgShowTools.input_shootDate.setDate(QDate.currentDate())

		self.wgShowTools.chk_renamePackage.setChecked(False)
		self.wgShowTools.input_remove.setText("")
		self.wgShowTools.input_prefix.setText("")
		self.wgShowTools.input_suffix.setText("")
		self.wgShowTools.chk_subfolderImages.setChecked(False)
		self.wgShowTools.chk_generateYAML.setChecked(False)
		self.wgShowTools.chk_notifyByEmail.setChecked(False)
		self.wgShowTools.chk_flagEmptyFolders.setChecked(False)

	def press_saveSettings(self):
		settings_data = self.get_pipeline_profile_data()

		file_path, _ = QFileDialog.getSaveFileName(
			self.wgShowTools,
			"Save Settings Profile",
			str(PIPELINE_PROFILES_PATH),
			"YAML Files (*.yaml *.yml)"
		)

		if not file_path:
			return

		if not file_path.lower().endswith((".yaml", ".yml")):
			file_path += ".yaml"

		try:
			with open(file_path, "w", encoding="utf-8") as yaml_file:
				yaml.dump(
					settings_data,
					yaml_file,
					default_flow_style=False,
					sort_keys=False
				)

			profile_name = os.path.basename(file_path)

			self.show_message(
				"Save Successful",
				"Settings Saved",
				profile_name,
				file_path
			)

		except Exception as error:
			self.show_message(
				"Save Failed",
				"Could not save settings.",
				str(error)
			)

	def press_export(self):

		folder_path = self.wgShowTools.input_targetFolder.text().strip()

		if not folder_path or not os.path.isdir(folder_path):
			self.show_message(
				"Export Failed",
				"Missing Target Folder",
				"Please select a valid target folder."
			)
			return

		original_folder_path = folder_path

		self.save_current_rule_settings()
		settings_data = self.get_settings_data()
		package_settings = settings_data.get("package_settings", {})

		rename_package = package_settings.get("rename_package", False)
		rename_remove = package_settings.get("remove", "")
		rename_prefix = package_settings.get("prefix", "")
		rename_suffix = package_settings.get("suffix", "")
		generate_yaml = package_settings.get("generate_yaml", False)
		create_revert_manifest = package_settings.get("create_revert_manifest", True)

		loading_dialog = LoadingDialog(self.wgShowTools)
		loading_dialog.show()
		QtWidgets.QApplication.processEvents()

		try:
			settings_data.setdefault("package_settings", {})
			settings_data["package_settings"]["slate_element_count"] = self.slate_element_count
			slate_result = run_slate_sorter(folder_path, settings_data)
			asset_result = run_asset_sorter(folder_path, settings_data)

			output_root = slate_result.get("final_path", folder_path)
			asset_output_root = asset_result.get("final_path", folder_path)

			# Prefer one shared root if either sorter resolved it
			if asset_output_root and asset_output_root != folder_path:
				output_root = asset_output_root

			manifest_root = slate_result.get("manifest_root", output_root)
			package_rename_target = slate_result.get("package_rename_target", manifest_root)

			empty_folders = []
			empty_folders.extend(slate_result.get("empty_folders", []))
			empty_folders.extend(asset_result.get("empty_folders", []))

			operations = []
			operations.extend(slate_result.get("operations", []))
			operations.extend(asset_result.get("operations", []))

			invalid_asset_folders = asset_result.get("invalid_asset_folders", [])

			flagged_count = 0

			if empty_folders:
				should_continue = self.confirm_empty_folders(empty_folders)

				if not should_continue:
					self.show_message(
						"Export Paused",
						"Empty Folders Found",
						"Export was paused so you can review the empty folders."
					)
					return

				flagged_paths = tag_empty_folders(empty_folders)
				flagged_count = len(flagged_paths)

			if invalid_asset_folders:
				invalid_count = len(invalid_asset_folders)
				print(f"Skipped {invalid_count} invalid asset folder(s):")
				for path in invalid_asset_folders:
					print("  ", path)

			final_output_root = output_root
			final_manifest_root = manifest_root
			final_package_target = package_rename_target

			if rename_package:
				pre_rename_path = package_rename_target

				renamed_path = rename_shoot_folder(
					package_rename_target,
					rename_remove=rename_remove,
					rename_prefix=rename_prefix,
					rename_suffix=rename_suffix
				)

				if renamed_path != pre_rename_path:
					operations.append({
						"type": "rename_package",
						"from": pre_rename_path,
						"to": renamed_path,
					})

					if final_package_target == pre_rename_path:
						final_package_target = renamed_path

					if final_manifest_root == pre_rename_path:
						final_manifest_root = renamed_path

					if final_output_root == pre_rename_path:
						final_output_root = renamed_path

			if create_revert_manifest:
				self.write_revert_manifest(
					final_root=final_manifest_root,
					original_root=original_folder_path,
					operations=operations,
					output_root=final_output_root,
				)

			if generate_yaml:
				try:
					print("Generating report...")
					generate_report.generate_report(final_output_root, settings_data)
					print("Report generation finished.")
				except Exception as report_error:
					print(f"Report generation failed: {report_error}")

			# In single-data-type mode, keep target attached to the selected folder
			self.set_target_folder(final_manifest_root)
			self.update_revert_button_state()

			package_name = os.path.basename(final_package_target)
			clean_package_name = package_name

			if rename_suffix:
				clean_package_name = clean_package_name.replace(rename_suffix, "")

			if rename_remove:
				clean_package_name = clean_package_name.replace(rename_remove, "")

			clean_package_name = clean_package_name.replace("__", "_").strip("_")

			context = {
				"package_name": package_name,
				"clean_package_name": clean_package_name,
				"project_name": self.wgShowTools.input_projectName.text().strip(),
				"wrangler": self.wgShowTools.input_wrangler.currentText().strip(),
				"unit": self.wgShowTools.input_unit.currentText().strip(),
				"shoot_date": self.wgShowTools.input_shootDate.date().toString("yyyy-MM-dd"),
			}

			email_subject = ""
			email_body = ""

			if hasattr(self, "email_defaults"):
				email_subject = self.format_email_text(
					self.email_defaults.get("subject", ""),
					context
				)
				email_body = self.format_email_text(
					self.email_defaults.get("body", ""),
					context
				)

				self.email_subject = email_subject
				self.email_body = email_body
				self.email_to = self.email_defaults.get("to", [])
				self.email_cc = self.email_defaults.get("cc", [])

			slates_path = os.path.join(final_output_root, "slates")

			if flagged_count == 1:
				detail_text = "1 folder was flagged as missing."
			elif flagged_count > 1:
				detail_text = f"{flagged_count} folders were flagged as missing."
			elif invalid_asset_folders:
				detail_text = f"Skipped {len(invalid_asset_folders)} invalid asset folder(s). See terminal for details."
			elif os.path.isdir(slates_path):
				detail_text = slates_path
			else:
				detail_text = final_manifest_root

			self.show_message(
				"Export Successful",
				"Sorting Complete",
				detail_text,
				final_manifest_root
			)

			if hasattr(self, "email_defaults") and self.wgShowTools.chk_notifyByEmail.isChecked():
				self.open_email_client(
					subject=self.email_subject,
					body=self.email_body,
					to_list=self.email_to,
					cc_list=self.email_cc
				)

		except Exception as error:
			self.show_message(
				"Export Failed",
				"Could not complete export.",
				str(error)
			)

		finally:
			loading_dialog.close()

	# PRESS BROWSE FILES
	def press_browseConfig(self):
		file_path, _ = QFileDialog.getOpenFileName(
			self.wgShowTools,
			"Select Pipeline Config",
			str(PIPELINE_PROFILES_PATH),
			"YAML Files (*.yaml *.yml);;All Files (*)"
		)

		if file_path:
			self.load_settings_from_yaml(file_path)

	def press_browseTargetFolder(self):
		current_path = self.wgShowTools.input_targetFolder.text().strip()

		folder = QtWidgets.QFileDialog.getExistingDirectory(
			self.wgShowTools,
			"Select Target Folder",
			current_path if current_path else ""
		)

		if folder:
			self.set_target_folder(folder)

	# PRESS LINKS
	def press_loadGmail(self):
		email = "harryshaper@gmail.com"
		subject = urllib.parse.quote("ShowTools Inquiry")
		body = urllib.parse.quote("Hi Harry,\n\n")

		url = (
			f"https://mail.google.com/mail/?view=cm"
			f"&to={email}"
			f"&su={subject}"
			f"&body={body}"
		)

		self.open_link(url)

	def press_loadGithub(self):
		self.open_link("https://github.com/HarryShaper")

	def press_loadLinkedin(self):
		self.open_link("https://www.linkedin.com/in/harry-shaper-vfx/")

	def press_loadYoutube(self):
		self.open_link("https://www.youtube.com/playlist?list=PLtRNjWjQ6iF6tMaf7kevFWNmKhQIWUwiI")

	def press_loadWebsite(self):
		self.open_link("https://www.shapervfx.com/")

	# *********************************************************************#
	# PRESS - RENAME SETTINGS PAGE
	#BUTTONS
	def edit_wranglers(self):

		current_wranglers = [
			self.wgShowTools.input_wrangler.itemText(i)
			for i in range(self.wgShowTools.input_wrangler.count())
		]

		dialog = WranglerDialog(
			current_wranglers,
			title_text="Manage Wranglers",
			subtitle_text="Add, rename, or remove wranglers for this show profile.",
			add_dialog_title="Add Wrangler",
			add_dialog_label="Wrangler Name:",
			parent=self.wgShowTools
		)

		if dialog.exec():

			new_wranglers = dialog.get_wranglers()

			self.wgShowTools.input_wrangler.clear()
			self.wgShowTools.input_wrangler.addItems(new_wranglers)

	def press_addRule(self):
		rule_number = len(self.rename_rules) + 1

		rule_data = {
			"name": f"CONVENTION {rule_number}",
			"data_type": "",
			"sort_by": "",
			"split_image_type": False,
			"delete_empty_folders": False,
			"naming_rule": "{ALL}",
		}

		self.rename_rules.append(rule_data)

		item = QtWidgets.QListWidgetItem()
		item.setSizeHint(QtCore.QSize(0, 44))  # controls row height

		widget = RuleListItemWidget(rule_data["name"])

		self.wgShowTools.list_rules.addItem(item)
		self.wgShowTools.list_rules.setItemWidget(item, widget)

		widget.btn_delete.clicked.connect(lambda: self.delete_rule_item(item))

		self.update_rules_list_height()

		new_index = self.wgShowTools.list_rules.count() - 1
		self.wgShowTools.list_rules.setCurrentRow(new_index)

		self.update_rule_editor_state()
		self.update_live_preview()
		self.update_add_rule_button_state()
		self.refresh_rule_item_selection_ui()

	def delete_rule_item(self, item):
		row = self.wgShowTools.list_rules.row(item)

		if row < 0:
			return

		rule_name = self.rename_rules[row].get("name", f"CONVENTION {row + 1}")

		should_delete = self.confirm_delete_rule(rule_name)
		if not should_delete:
			return

		self.wgShowTools.list_rules.takeItem(row)
		del self.rename_rules[row]

		if not self.rename_rules:
			self.current_rule_index = None
		else:
			new_row = min(row, len(self.rename_rules) - 1)
			self.wgShowTools.list_rules.setCurrentRow(new_row)

		self.update_rules_list_height()
		self.update_add_rule_button_state()
		self.update_rule_editor_state()
		self.update_live_preview()
		self.refresh_rule_item_selection_ui()

	def press_clearNamingRule(self):
		"""Reset the naming rule back to the default original-name token."""
		self.wgShowTools.input_namingRule.setText("{ALL}")
		self.wgShowTools.input_namingRule.setFocus()

	def press_revert(self):
		folder_path = self.wgShowTools.input_targetFolder.text().strip()

		if not folder_path or not os.path.isdir(folder_path):
			self.show_message(
				"Revert Unavailable",
				"Missing Target Folder",
				"Please select a valid processed folder."
			)
			return

		manifest_data = self.read_revert_manifest(folder_path)
		manifest_path = self.get_revert_manifest_path(folder_path)

		if not self.validate_revert_manifest(manifest_path, folder_path):
			self.show_message(
				"Revert Unavailable",
				"No valid revert manifest found.",
				"Select a processed ShowTools package to enable revert."
			)
			return

		should_revert = self.confirm_revert_sort()
		if not should_revert:
			return

		result = self.revert_operations_from_manifest(folder_path)
		messages = result.get("messages", [])

		manifest = (manifest_data or {}).get("export_manifest", {})
		original_root = manifest.get("original_root", "")
		output_root = manifest.get("output_root", "")

		log_path = None

		# Only write debug log if something failed
		if not result.get("success", False):
			log_target = original_root if original_root and os.path.exists(original_root) else folder_path
			log_path = self.write_revert_debug_log(log_target, messages)

		# Always attempt cleanup
		cleanup_root = None

		if original_root and os.path.exists(original_root):
			cleanup_root = original_root
		elif output_root and os.path.exists(output_root):
			cleanup_root = output_root

		if cleanup_root:
			slates_path = Path(cleanup_root) / "SLATES"
			assets_path = Path(cleanup_root) / "ASSETS"

			self.remove_empty_dir_tree(slates_path)
			self.remove_empty_dir_tree(assets_path)

		# Remove manifests from both possible locations
		self.remove_revert_manifest(folder_path)
		if original_root:
			self.remove_revert_manifest(original_root)

		# If original root exists, point UI back there
		if original_root and os.path.exists(original_root):
			self.set_target_folder(original_root)

		self.update_revert_button_state()

		if result.get("success", False):
			self.show_message(
				"Revert Successful",
				"Sort was reversed successfully.",
				original_root if original_root else folder_path
			)
		else:
			self.show_message(
				"Revert Completed With Warnings",
				"Some operations could not be fully reverted.",
				str(log_path) if log_path else "See terminal/log for details."
			)
		
	def remove_revert_manifest(self, folder_path):
		manifest_path = self.get_revert_manifest_path(folder_path)
		if not manifest_path:
			return

		try:
			if manifest_path.is_file():
				os.remove(manifest_path)

			manifest_dir = manifest_path.parent

			# Only remove .showtools if empty
			if manifest_dir.exists() and not any(manifest_dir.iterdir()):
				manifest_dir.rmdir()

		except Exception as error:
			print(f"Failed to remove revert manifest: {error}")

	#NAME TOKENS
	def press_btn_token_first(self):
		self.insert_naming_token("{FIRST}")

	def press_btn_token_middle(self):
		self.insert_naming_token("{REST}")

	def press_btn_token_last(self):
		self.insert_naming_token("{LAST}")

	def press_btn_token_all(self):
		self.insert_naming_token("{ALL}")

	#METADATA TOKENS
	def press_btn_token_slate(self):
		self.insert_naming_token("{SLATE}")

	def press_btn_token_wrangler(self):
		self.insert_naming_token("{WRANGLER}")

	def press_btn_token_unit(self):
		self.insert_naming_token("{UNIT}")

	def press_btn_token_date(self):
		self.insert_naming_token("{DATE}")

	def press_btn_token_project(self):
		self.insert_naming_token("{PROJECT}")

	def press_btn_token_shoot_date(self):
		self.insert_naming_token("{SHOOT_DATE}")

	def press_btn_token_data_type(self):
		self.insert_naming_token("{DATA_TYPE}")

	def press_btn_token_focal(self):
		self.insert_naming_token("{FOCAL}")
	

# *********************************************************************#
# START UI
if __name__ == "__main__":
	try:
		app = QtWidgets.QApplication(sys.argv)
		initialize_app = ShowTools()
		app.exec()
	except Exception as error:
		import traceback
		traceback.print_exc()
		input("Press Enter to close...")