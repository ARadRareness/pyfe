from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QTreeView,
    QHeaderView,
    QSplitter,
    QAbstractItemView,
    QMenu,
    QFileSystemModel,
)
from PySide6.QtGui import (
    QStandardItemModel,
    QStandardItem,
    QIcon,
    QDesktopServices,
    QAction,
    QKeySequence,
    QShortcut,
)
from PySide6.QtCore import (
    Qt,
    QDir,
    QUrl,
    QFileInfo,
    QSortFilterProxyModel,
)

import os
import math

from interface import file_actions
from interface.custom_widgets import NoHighlightDelegate
from interface.icon_mapper import IconMapper
from interface.navigation_manager import NavigationManager
from interface.favorites_manager import FavoritesManager
from interface.system_menu_manager import SystemMenuManager
from interface.toolbar_manager import ToolbarManager  # Add this import


class FileExplorerUI(QMainWindow):
    def __init__(self, base_dir: str):
        super().__init__()
        self.setWindowTitle("Python File Explorer")
        self.setGeometry(100, 100, 800, 600)

        self.base_dir = base_dir
        self.set_window_icon()

        file_system_model = QFileSystemModel()
        file_system_model.setRootPath("")

        self.icon_mapper = IconMapper(self.base_dir)
        self.navigation_manager = NavigationManager()
        self.favorites_manager = FavoritesManager(self.base_dir)
        self.toolbar_manager = ToolbarManager(self, self.base_dir, file_system_model)
        self.system_menu_manager = SystemMenuManager(self)

        self.navigation_manager.path_changed.connect(self.update_view)
        self.init_interface()

        self.model = QStandardItemModel()
        self.proxy_model = QSortFilterProxyModel(self)
        self.proxy_model.setSourceModel(self.model)
        self.tree_view.setModel(self.proxy_model)

        # Set default sorting
        self.tree_view.sortByColumn(0, Qt.AscendingOrder)
        self.proxy_model.setSortRole(Qt.UserRole)

        self.update_view()

        self.clipboard = []
        self.setup_shortcuts()

    def init_interface(self):
        main_layout = QVBoxLayout()

        # Create toolbar using ToolbarManager
        toolbar = self.toolbar_manager.create_toolbar()
        main_layout.addLayout(toolbar)

        # Create splitter to hold the left and right views
        self.splitter = QSplitter(Qt.Horizontal)

        # Create left view for favorite folders
        self.splitter.addWidget(self.favorites_manager.get_view())

        # Create tree view for file explorer
        self.create_tree_view()
        self.splitter.addWidget(self.tree_view)

        # Set the initial sizes of the splitter
        self.splitter.setSizes([150, 650])
        self.splitter.setStretchFactor(0, 0)
        self.splitter.setStretchFactor(1, 1)

        main_layout.addWidget(self.splitter)

        # Set up central widget
        central_widget = QWidget()
        central_widget.setLayout(main_layout)
        self.setCentralWidget(central_widget)

        # Connect signals
        self.connect_signals()

    def create_tree_view(self):
        self.tree_view = QTreeView()
        self.tree_view.setUniformRowHeights(True)
        self.tree_view.header().setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        self.tree_view.setItemDelegate(NoHighlightDelegate(self.tree_view))
        self.tree_view.setSelectionMode(QTreeView.ExtendedSelection)
        self.tree_view.setEditTriggers(QTreeView.NoEditTriggers)
        self.tree_view.setVerticalScrollMode(QAbstractItemView.ScrollPerPixel)
        self.tree_view.setContextMenuPolicy(Qt.CustomContextMenu)
        self.tree_view.customContextMenuRequested.connect(self.show_context_menu)

        self.tree_view.setSortingEnabled(True)
        self.tree_view.header().setSortIndicator(0, Qt.AscendingOrder)

    def connect_signals(self):
        self.toolbar_manager.connect_signals(self.navigation_manager)
        self.tree_view.doubleClicked.connect(self.on_double_click)
        self.favorites_manager.get_view().clicked.connect(self.on_favorite_click)

    def set_window_icon(self):
        icon_path = os.path.join(self.base_dir, "icons", "icon.png")
        self.setWindowIcon(QIcon(icon_path))

    def setup_shortcuts(self):
        QShortcut(QKeySequence.Copy, self.tree_view, self.copy_clipboard)
        QShortcut(QKeySequence.Paste, self.tree_view, self.paste_clipboard)
        # QShortcut(QKeySequence.Cut, self.tree_view, self.cut_selected)
        QShortcut(QKeySequence.Delete, self.tree_view, self.delete_selected)

    def copy_clipboard(self):
        self.clipboard = []
        for index in self.tree_view.selectedIndexes():
            if index.column() == 0:  # Only process the first column
                source_index = self.proxy_model.mapToSource(index)
                item = self.model.itemFromIndex(source_index)
                if item:
                    file_path = os.path.join(self.current_path, item.text())
                    self.clipboard.append(file_path)
                else:
                    print(
                        f"Warning: Invalid item at index {index.row()}, {index.column()}"
                    )

        if not self.clipboard:
            print("No valid items selected for copying")
        else:
            print(f"Copied {len(self.clipboard)} item(s) to clipboard")

    def paste_clipboard(self):
        files_copied = file_actions.copy_files(self.clipboard, self.current_path)

        if files_copied:
            self.update_view()

    def delete_selected(self):
        selected_indexes = self.tree_view.selectedIndexes()
        if not selected_indexes:
            return

        # Get unique rows (files/folders) to delete
        rows_to_delete = set(index.row() for index in selected_indexes)
        items_to_delete = [self.model.item(row, 0).text() for row in rows_to_delete]

        files_deleted = file_actions.delete_files(
            self, items_to_delete, self.current_path
        )

        if files_deleted:
            self.update_view()

    def update_view(self):
        # Save current column sizes
        column_sizes = [
            self.tree_view.columnWidth(i) for i in range(self.model.columnCount())
        ]

        self.model.clear()
        self.model.setHorizontalHeaderLabels(["Name", "Date Modified", "Type", "Size"])

        # Set a larger default width for the Name column
        self.tree_view.setColumnWidth(0, 300)  # Adjust this value as needed

        # Restore column sizes for other columns
        for i, size in enumerate(column_sizes[1:], start=1):
            self.tree_view.setColumnWidth(i, size)

        self.current_path = self.navigation_manager.current_path
        self.toolbar_manager.update_address_bar(self.current_path)

        self.load_directory_contents()

        self.update_navigation_buttons()

        self.proxy_model.sort(0, Qt.AscendingOrder)

    def load_directory_contents(self):
        directory = QDir(self.current_path)
        folders = []
        files = []

        for file_info in directory.entryInfoList():
            if file_info.fileName() in (".", ".."):
                continue

            size_kb = math.ceil(file_info.size() / 1024)
            size_str = f"{size_kb} KB" if file_info.isFile() else ""
            item_data = [
                file_info.fileName(),
                file_info.lastModified().toString("yyyy-MM-dd HH:mm:ss"),
                "File folder" if file_info.isDir() else file_info.suffix(),
                size_str,
                file_info.isDir(),
            ]

            if file_info.isDir():
                folders.append(item_data)
            else:
                files.append(item_data)

        # Add ".." only if there's a parent directory
        if self.navigation_manager.can_go_up():
            parent_data = ["..", "", "File folder", "", True]
            self.add_file_item(parent_data, True, is_parent=True)

        # Process folders
        for folder in folders:
            self.add_file_item(folder, True)

        # Process files
        for file in files:
            self.add_file_item(file, False)

    def add_file_item(self, file_data, is_dir, is_parent=False):
        name, date, file_type, size, _ = file_data
        name_item = QStandardItem(name)
        name_item.setIcon(
            self.icon_mapper.get_icon(os.path.join(self.current_path, name))
        )

        # Set custom sort role data
        name_item.setData(0 if is_parent else (1 if is_dir else 2), Qt.UserRole)
        name_item.setData(name.lower(), Qt.UserRole + 1)

        date_item = QStandardItem(date)
        date_item.setData(
            QFileInfo(os.path.join(self.current_path, name)).lastModified(), Qt.UserRole
        )

        type_item = QStandardItem(file_type)
        type_item.setData(file_type.lower(), Qt.UserRole)

        size_item = QStandardItem(size)
        size_item.setData(int(size.split()[0]) if size else -1, Qt.UserRole)

        self.model.appendRow([name_item, date_item, type_item, size_item])

    def on_double_click(self, index):
        if QApplication.mouseButtons() == Qt.LeftButton:
            # Convert the proxy model index to the source model index
            source_index = self.proxy_model.mapToSource(index)
            item = self.model.itemFromIndex(source_index)
            if item:
                file_name = item.text()
                if file_name == "..":
                    self.navigation_manager.go_up()
                else:
                    new_path = os.path.normpath(
                        QDir(self.current_path).filePath(file_name)
                    )
                    file_info = QFileInfo(new_path)
                    if file_info.exists():
                        if file_info.isDir():
                            self.navigation_manager.navigate_to(new_path)
                        else:
                            QDesktopServices.openUrl(QUrl.fromLocalFile(new_path))

    def on_favorite_click(self, index):
        item = self.favorites_manager.favorites_model.itemFromIndex(index)
        if item and item.data(Qt.UserRole + 1) != "delimiter":
            path = item.data(Qt.UserRole)
            if QDir(path).exists():
                self.navigation_manager.navigate_to(path)

    def navigate_to(self, path):
        if path != self.current_path:
            self.history_backward.append(self.current_path)
            self.history_forward.clear()
            self.current_path = path
            self.update_view()

    def go_back(self):
        if self.history_backward:
            self.history_forward.append(self.current_path)
            self.current_path = self.history_backward.pop()
            self.update_view()

    def go_forward(self):
        if self.history_forward:
            self.history_backward.append(self.current_path)
            self.current_path = self.history_forward.pop()
            self.update_view()

    def go_up(self):
        parent_path = QDir(self.current_path).filePath("..")
        self.navigate_to(QDir(parent_path).absolutePath())

    def update_navigation_buttons(self):
        can_go_back = self.navigation_manager.can_go_back()
        can_go_forward = self.navigation_manager.can_go_forward()
        can_go_up = self.navigation_manager.can_go_up()
        self.toolbar_manager.update_navigation_buttons(can_go_back, can_go_forward)
        self.toolbar_manager.update_up_button(can_go_up)

    def change_directory(self):
        new_path = self.toolbar_manager.address_bar.text()
        if QDir(new_path).exists():
            self.navigation_manager.navigate_to(new_path)

    def show_context_menu(self, position):
        # Convert the position to an index in the proxy model
        proxy_index = self.tree_view.indexAt(position)
        if proxy_index.isValid():
            # Map the proxy index to the source model index
            source_index = self.proxy_model.mapToSource(proxy_index)
            item = self.model.itemFromIndex(source_index)
            file_name = item.text()
            file_path = os.path.join(self.current_path, file_name)

            # Don't show the context menu for ".."
            if file_name == "..":
                return

            context_menu = QMenu(self)

            if os.path.isdir(file_path):
                star_action = QAction("Star folder", self)
                star_action.triggered.connect(lambda: self.star_folder(file_path))
                context_menu.addAction(star_action)

                # Disable the action if the folder is already in favorites
                star_action.setEnabled(
                    not self.favorites_manager.is_folder_in_favorites(file_path)
                )
            else:
                # Add actions for files here
                open_action = QAction("Open", self)
                open_action.triggered.connect(
                    lambda: QDesktopServices.openUrl(QUrl.fromLocalFile(file_path))
                )
                context_menu.addAction(open_action)

            # Add common actions for both files and folders
            copy_action = QAction("Copy", self)
            copy_action.triggered.connect(self.copy_clipboard)
            context_menu.addAction(copy_action)

            delete_action = QAction("Delete", self)
            delete_action.triggered.connect(self.delete_selected)
            context_menu.addAction(delete_action)

            context_menu.exec(self.tree_view.viewport().mapToGlobal(position))

    def star_folder(self, folder_path):
        self.favorites_manager.star_folder(folder_path)

    def filter_view(self):
        search_text = self.toolbar_manager.get_search_text()
        # Implement the filtering logic here
        # For example, you can hide/show items in the tree_view based on the search_text
