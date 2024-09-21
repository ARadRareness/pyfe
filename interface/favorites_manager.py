from PySide6.QtWidgets import QListView
from PySide6.QtGui import QStandardItemModel, QStandardItem, QIcon, QBrush, QColor
from PySide6.QtCore import Qt, QSize, QDir
import os
import sys


class FavoritesManager:
    def __init__(self, base_dir):
        self.base_dir = base_dir
        self.favorites_view = QListView()
        self.favorites_model = QStandardItemModel()
        self.favorites_view.setModel(self.favorites_model)
        self.favorites_view.setEditTriggers(QListView.NoEditTriggers)
        self.favorites_view.setSelectionMode(QListView.NoSelection)
        self.populate_favorites()
        self.add_favorites_delimiter()

    def populate_favorites(self):
        favorites = [
            ("Home", QDir.homePath()),
            ("Desktop", QDir.homePath() + "/Desktop"),
            ("Documents", QDir.homePath() + "/Documents"),
            ("Downloads", QDir.homePath() + "/Downloads"),
            ("Pictures", QDir.homePath() + "/Pictures"),
            ("Music", QDir.homePath() + "/Music"),
            ("Videos", QDir.homePath() + "/Videos"),
            ("Dropbox", QDir.homePath() + "/Dropbox"),
        ]

        if sys.platform == "win32":
            import win32api

            drives = win32api.GetLogicalDriveStrings().split("\000")[:-1]
            favorites.extend(
                (drive.rstrip("\\"), drive.rstrip("\\")) for drive in drives
            )

        for name, path in favorites:
            if os.path.exists(path):
                self.add_favorite_item(name, path, "default")

    def add_favorites_delimiter(self):
        delimiter_item = QStandardItem()
        delimiter_item.setEnabled(False)
        delimiter_item.setData("delimiter", Qt.UserRole + 1)
        delimiter_item.setBackground(QBrush(QColor(200, 200, 200)))
        delimiter_item.setSizeHint(QSize(0, 4))
        self.favorites_model.appendRow(delimiter_item)

    def add_favorite_item(self, name, path, item_type):
        item = QStandardItem(name)
        item.setData(path, Qt.UserRole)
        item.setData(item_type, Qt.UserRole + 1)
        icon_path = os.path.join(self.base_dir, "icons", "folder.png")
        item.setIcon(QIcon(icon_path))

        if item_type == "starred":
            insert_position = self.get_insert_position(name)
            self.favorites_model.insertRow(insert_position, item)
        else:
            self.favorites_model.appendRow(item)

    def get_insert_position(self, folder_name):
        insert_position = self.favorites_model.rowCount()
        for row in range(self.favorites_model.rowCount()):
            current_item = self.favorites_model.item(row)
            if current_item.data(Qt.UserRole + 1) == "delimiter":
                insert_position = row + 1
                break

        while insert_position < self.favorites_model.rowCount():
            current_item = self.favorites_model.item(insert_position)
            if current_item.text().lower() > folder_name.lower():
                break
            insert_position += 1

        return insert_position

    def is_folder_in_favorites(self, folder_path):
        for row in range(self.favorites_model.rowCount()):
            item = self.favorites_model.item(row)
            if (
                item.data(Qt.UserRole + 1) != "delimiter"
                and item.data(Qt.UserRole) == folder_path
            ):
                return True
        return False

    def star_folder(self, folder_path):
        if not self.is_folder_in_favorites(folder_path):
            folder_name = os.path.basename(folder_path)
            self.add_favorite_item(folder_name, folder_path, "starred")

    def get_view(self):
        return self.favorites_view
