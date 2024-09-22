import shutil
from PySide6.QtWidgets import QMessageBox, QMenu, QInputDialog
from PySide6.QtGui import QDesktopServices, QAction
from PySide6.QtCore import QUrl, QSettings
import os
from send2trash import send2trash
from .file_conversion.epub.epub_manager import EpubManager
from .file_conversion.multimedia.multimedia_manager import MultimediaManager
from .file_conversion.text.text_manager import TextManager


class FileActionManager:
    def __init__(self, app):
        self.app = app
        self.settings = QSettings("ARadRareness", "PythonFileExplorer")
        self.special_interactions = {}
        self.epub_manager = EpubManager(app)
        self.multimedia_manager = MultimediaManager(app)
        self.text_manager = TextManager(app)
        self.init_interactions()

    def init_interactions(self):
        # Define special interactions here
        self.special_interactions = {
            ".epub": self.epub_manager.get_actions(),
            ".mp3": self.multimedia_manager.get_actions(".mp3"),
            ".mp4": self.multimedia_manager.get_actions(".mp4"),
            ".txt": self.text_manager.get_actions(),
        }

    def delete_files(self, items_to_delete, current_path):
        files_deleted = []
        current_path = os.path.normpath(current_path)

        msg_box = QMessageBox(parent=self.app)
        msg_box.setText(
            f"Are you sure you want to move {len(items_to_delete)} item(s) to the trash?"
        )
        msg_box.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        msg_box.setDefaultButton(QMessageBox.Yes)

        if msg_box.exec() == QMessageBox.Yes:
            for item_name in items_to_delete:
                item_path = os.path.join(current_path, item_name)
                try:
                    send2trash(item_path)
                    files_deleted.append(item_path)
                except Exception as e:
                    QMessageBox.critical(
                        self.app,
                        "Error",
                        f"Failed to move {item_name} to trash: {str(e)}",
                    )

        return files_deleted

    def copy_files(self, items_to_copy, current_path):
        copied_files = []
        for source_path in items_to_copy:
            if not os.path.exists(source_path):
                continue

            copied_files.append(source_path)
            file_name = os.path.basename(source_path)
            destination_path = os.path.join(current_path, file_name)

            if os.path.exists(destination_path):
                # Handle name conflicts
                base, ext = os.path.splitext(file_name)
                counter = 1
                while os.path.exists(destination_path):
                    new_name = f"{base} ({counter}){ext}"
                    destination_path = os.path.join(current_path, new_name)
                    counter += 1

            try:
                if os.path.isdir(source_path):
                    shutil.copytree(source_path, destination_path)
                else:
                    shutil.copy2(source_path, destination_path)
            except Exception as e:
                print(f"Error copying {source_path}: {str(e)}")

        return copied_files

    def show_context_menu(
        self, position, tree_view, model, proxy_model, current_path, favorites_manager
    ):
        proxy_index = tree_view.indexAt(position)
        if proxy_index.isValid():
            source_index = proxy_model.mapToSource(proxy_index)
            item = model.itemFromIndex(source_index)
            file_name = item.text()
            file_path = os.path.join(current_path, file_name)

            if file_name == "..":
                return

            context_menu = QMenu(self.app)

            # Existing menu items
            if os.path.isdir(file_path):
                star_action = QAction("Star folder", self.app)
                star_action.triggered.connect(
                    lambda: favorites_manager.star_folder(file_path)
                )
                context_menu.addAction(star_action)
                star_action.setEnabled(
                    not favorites_manager.is_folder_in_favorites(file_path)
                )
            else:
                open_action = QAction("Open", self.app)
                open_action.triggered.connect(
                    lambda: QDesktopServices.openUrl(QUrl.fromLocalFile(file_path))
                )
                context_menu.addAction(open_action)

            # Add rename action
            rename_action = QAction("Rename", self.app)
            rename_action.triggered.connect(
                lambda: self.rename_item(item, current_path)
            )
            context_menu.addAction(rename_action)

            copy_action = QAction("Copy", self.app)
            copy_action.triggered.connect(self.app.copy_clipboard)
            context_menu.addAction(copy_action)

            # Add paste action
            paste_action = QAction("Paste", self.app)
            paste_action.triggered.connect(self.app.paste_clipboard)
            paste_action.setEnabled(
                bool(self.app.clipboard)
            )  # Enable only if clipboard is not empty
            context_menu.addAction(paste_action)

            delete_action = QAction("Delete", self.app)
            delete_action.triggered.connect(self.app.delete_selected)
            context_menu.addAction(delete_action)

            # Add file-specific actions based on file extension
            _, file_extension = os.path.splitext(file_name)
            if file_extension.lower() in self.special_interactions:
                for interaction in self.special_interactions[file_extension.lower()]:
                    # Check if the action should be shown based on AI mode
                    if interaction.get(
                        "ai_only", False
                    ) == True and not self.settings.value(
                        "enable_ai", False, type=bool
                    ):
                        continue

                    action = QAction(interaction["name"], self.app)
                    if "icon" in interaction:
                        action.setIcon(interaction["icon"])
                    action.triggered.connect(
                        lambda checked, f=file_path, a=interaction[
                            "action"
                        ]: self.handle_special_interaction(f, a)
                    )
                    context_menu.addAction(action)

            # Add separator before the "New" submenu
            context_menu.addSeparator()

            # Modify the "New" submenu creation
            new_menu = QMenu("New", context_menu)
            new_file_action = QAction(
                self.app.icon_mapper.text_file_icon, "File", new_menu
            )
            new_folder_action = QAction(
                self.app.icon_mapper.folder_icon, "Folder", new_menu
            )
            new_menu.addAction(new_file_action)
            new_menu.addAction(new_folder_action)
            context_menu.addMenu(new_menu)

            # Connect actions to appropriate methods
            new_file_action.triggered.connect(
                lambda: self.create_new_file(current_path)
            )
            new_folder_action.triggered.connect(
                lambda: self.create_new_folder(current_path)
            )

            context_menu.exec(tree_view.viewport().mapToGlobal(position))

    def handle_special_interaction(self, file_path, action):
        result = action(file_path)
        if result is True:
            self.app.update_view()

    def create_new_file(self, current_path):
        file_name, ok = QInputDialog.getText(self.app, "New File", "Enter file name:")
        if ok and file_name:
            file_path = os.path.join(current_path, file_name)
            try:
                with open(file_path, "w") as f:
                    pass  # Create an empty file
                self.app.update_view()
            except Exception as e:
                QMessageBox.critical(
                    self.app, "Error", f"Failed to create file: {str(e)}"
                )

    def create_new_folder(self, current_path):
        folder_name, ok = QInputDialog.getText(
            self.app, "New Folder", "Enter folder name:"
        )
        if ok and folder_name:
            folder_path = os.path.join(current_path, folder_name)
            try:
                os.mkdir(folder_path)
                self.app.update_view()
            except Exception as e:
                QMessageBox.critical(
                    self.app, "Error", f"Failed to create folder: {str(e)}"
                )

    def show_empty_context_menu(self, position, tree_view, current_path):
        context_menu = QMenu(self.app)

        # Add paste action
        paste_action = QAction("Paste", self.app)
        paste_action.triggered.connect(self.app.paste_clipboard)
        paste_action.setEnabled(
            bool(self.app.clipboard)
        )  # Enable only if clipboard is not empty
        context_menu.addAction(paste_action)

        # Add a separator
        context_menu.addSeparator()

        # Modify the "New" submenu creation
        new_menu = QMenu("New", context_menu)
        new_file_action = QAction(self.app.icon_mapper.text_file_icon, "File", new_menu)
        new_folder_action = QAction(
            self.app.icon_mapper.folder_icon, "Folder", new_menu
        )
        new_menu.addAction(new_file_action)
        new_menu.addAction(new_folder_action)
        context_menu.addMenu(new_menu)

        # Connect actions to appropriate methods
        new_file_action.triggered.connect(lambda: self.create_new_file(current_path))
        new_folder_action.triggered.connect(
            lambda: self.create_new_folder(current_path)
        )

        context_menu.exec(tree_view.viewport().mapToGlobal(position))

    def rename_item(self, item, current_path):
        old_name = item.text()
        new_name, ok = QInputDialog.getText(
            self.app, "Rename", "Enter new name:", text=old_name
        )
        if ok and new_name and new_name != old_name:
            old_path = os.path.join(current_path, old_name)
            new_path = os.path.join(current_path, new_name)
            try:
                os.rename(old_path, new_path)
                self.app.update_view()  # Add this line to update the view
                return True
            except OSError as e:
                QMessageBox.critical(self.app, "Error", f"Failed to rename: {str(e)}")
        return False
