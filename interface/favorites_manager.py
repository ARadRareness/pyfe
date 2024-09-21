from PySide6.QtWidgets import QListView, QMenu, QMessageBox
from PySide6.QtGui import QStandardItemModel, QStandardItem, QIcon, QBrush, QColor
from PySide6.QtCore import Qt, QSize, QDir, QSettings
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
        self.favorites_view.setContextMenuPolicy(Qt.CustomContextMenu)
        self.favorites_view.customContextMenuRequested.connect(self.show_context_menu)

        self.settings = QSettings("ARadRareness", "PythonFileExplorer")

        self.populate_favorites()
        self.add_favorites_delimiter()
        self.load_starred_folders()

    def populate_favorites(self):
        home_path = os.path.normpath(QDir.homePath())
        favorites = [
            ("Home", home_path),
            ("Desktop", os.path.join(home_path, "Desktop")),
            ("Documents", os.path.join(home_path, "Documents")),
            ("Downloads", os.path.join(home_path, "Downloads")),
            ("Pictures", os.path.join(home_path, "Pictures")),
            ("Music", os.path.join(home_path, "Music")),
            ("Videos", os.path.join(home_path, "Videos")),
            ("Dropbox", os.path.join(home_path, "Dropbox")),
        ]

        if sys.platform == "win32":
            import win32api

            drives = win32api.GetLogicalDriveStrings().split("\000")[:-1]
            favorites.extend((drive.rstrip("\\"), drive) for drive in drives)

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
            self.save_starred_folders()

    def show_context_menu(self, position):
        index = self.favorites_view.indexAt(position)
        if not index.isValid():
            return

        item = self.favorites_model.itemFromIndex(index)
        if item.data(Qt.UserRole + 1) == "starred":
            menu = QMenu()
            remove_action = menu.addAction("Remove")
            action = menu.exec_(self.favorites_view.viewport().mapToGlobal(position))

            if action == remove_action:
                self.confirm_remove_favorite(item)

    def is_drive(self, path):
        if sys.platform == "win32":
            return os.path.splitdrive(path)[1] == "\\"
        return False

    def confirm_remove_favorite(self, item):
        folder_name = item.text()
        msg_box = QMessageBox()
        msg_box.setIcon(QMessageBox.Question)
        msg_box.setText(f"Do you want to remove {folder_name} from favorites?")
        msg_box.setWindowTitle("Remove Favorite")
        msg_box.setStandardButtons(QMessageBox.Yes | QMessageBox.No)

        if msg_box.exec_() == QMessageBox.Yes:
            self.remove_favorite(item)

    def remove_favorite(self, item):
        if item.data(Qt.UserRole + 1) == "starred":
            self.favorites_model.removeRow(item.row())
            self.save_starred_folders()

    def get_view(self):
        return self.favorites_view

    def load_starred_folders(self):
        starred_folders = self.settings.value("starred_folders", [])
        for name, path in starred_folders:
            if os.path.exists(path):
                self.add_favorite_item(name, path, "starred")

    def save_starred_folders(self):
        starred_folders = []
        for row in range(self.favorites_model.rowCount()):
            item = self.favorites_model.item(row)
            if item.data(Qt.UserRole + 1) == "starred":
                starred_folders.append((item.text(), item.data(Qt.UserRole)))

        self.settings.setValue("starred_folders", starred_folders)
