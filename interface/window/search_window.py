from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QLabel,
    QAbstractItemView,
    QHBoxLayout,
    QLineEdit,
    QPushButton,
    QFileDialog,
)
from PySide6.QtCore import Qt, QThread, Signal, QFileInfo
from PySide6.QtWidgets import QMainWindow
import os
import sys
import math
import uuid  # Add this import

from PySide6.QtGui import QShowEvent, QCloseEvent, QKeyEvent


class SearchThread(QThread):
    result_found = Signal(str, str, str, str, str, str)  # Add search_id to the signal
    finished = Signal(str)  # Add search_id to the finished signal

    def __init__(
        self, root_path: str, name_query: str, content_query: str, search_id: str
    ):
        super().__init__()
        self.root_path = root_path
        self.content_query = content_query
        self.include_terms, self.exclude_terms = self.parse_query(name_query)
        self.stop_flag = False
        self.search_id = search_id  # Store the search_id

    def parse_query(self, query: str) -> tuple[list[str], list[str]]:
        include_terms = []
        exclude_terms = []
        current_phrase = []
        in_quotes = False
        excluding = False
        for word in query.lower().split():
            if word.startswith("-"):
                excluding = True
                word = word[1:]  # Remove the leading '-'

            if word.startswith('"') and word.endswith('"'):
                term = word.strip('"')
                (exclude_terms if excluding else include_terms).append(term)
                excluding = False
            elif word.startswith('"'):
                in_quotes = True
                current_phrase = [word.strip('"')]
            elif word.endswith('"'):
                in_quotes = False
                current_phrase.append(word.strip('"'))
                term = " ".join(current_phrase)
                (exclude_terms if excluding else include_terms).append(term)
                current_phrase = []
                excluding = False
            elif in_quotes:
                current_phrase.append(word)
            else:
                (exclude_terms if excluding else include_terms).append(word)
                excluding = False

        if current_phrase:
            term = " ".join(current_phrase)
            (exclude_terms if excluding else include_terms).append(term)

        return include_terms, exclude_terms

    def match_query(self, name: str) -> bool:
        name_lower = name.lower()

        # Check exclude terms first
        for term in self.exclude_terms:
            if term in name_lower:
                return False

        # Then check include terms
        for term in self.include_terms:
            if " " in term:
                # Quoted phrase: must match exactly
                if term not in name_lower:
                    return False
            else:
                # Single word: must exist somewhere in the name
                if term not in name_lower:
                    return False

        return True

    def run(self):
        for root, dirs, files in os.walk(self.root_path, topdown=True):
            if self.stop_flag:
                break

            # Skip protected directories only if we're on macOS and at the root level
            if sys.platform == "darwin" and root == "/":
                dirs[:] = [d for d in dirs if not self.is_protected_directory(d)]

            for name in dirs + files:
                if self.stop_flag:
                    break
                if self.match_query(name):
                    full_path = os.path.join(root, name)
                    file_info = QFileInfo(full_path)
                    date_modified = file_info.lastModified().toString(
                        "yyyy-MM-dd HH:mm:ss"
                    )
                    file_type = (
                        "File folder" if file_info.isDir() else file_info.suffix()
                    )
                    size_kb = math.ceil(file_info.size() / 1024)
                    size = f"{size_kb} KB" if file_info.isFile() else ""
                    if not self.stop_flag:
                        self.result_found.emit(
                            name,
                            full_path,
                            date_modified,
                            file_type,
                            size,
                            self.search_id,
                        )

        self.finished.emit(self.search_id)

    def is_protected_directory(self, dirname: str) -> bool:
        protected_dirs = [
            "Library",
            "System",
            "private",
            "cores",
            "etc",
            "var",
            "usr",
            "bin",
            "sbin",
            "opt",
            "Applications",
        ]
        return dirname in protected_dirs

    def stop(self):
        self.stop_flag = True


class SearchWindow(QWidget):
    def __init__(self, parent: QMainWindow):
        super().__init__(parent)
        self.setWindowTitle("Search Results")
        self.setGeometry(200, 200, 1000, 600)
        self.setWindowFlags(Qt.WindowType.Window)

        layout = QVBoxLayout()

        # Add search input fields
        search_layout = QHBoxLayout()

        search_layout.addWidget(QLabel("Name:"))
        self.name_input = QLineEdit()
        search_layout.addWidget(self.name_input)

        search_layout.addWidget(QLabel("Path:"))
        self.path_input = QLineEdit()
        self.path_input.setReadOnly(True)
        search_layout.addWidget(self.path_input)

        self.browse_button = QPushButton("Browse...")
        self.browse_button.clicked.connect(self.browse_directory)
        search_layout.addWidget(self.browse_button)

        search_layout.addWidget(QLabel("Content:"))
        self.content_input = QLineEdit()
        search_layout.addWidget(self.content_input)

        layout.addLayout(search_layout)

        # Existing table widget setup
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(
            ["Name", "Path", "Date Modified", "Type", "Size"]
        )
        self.table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Interactive
        )
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.verticalHeader().setVisible(False)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.cellDoubleClicked.connect(self.navigate_to_item)
        self.table.itemSelectionChanged.connect(self.on_selection_changed)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)

        # Set column widths similar to the file explorer
        self.table.setColumnWidth(0, 300)  # Name column
        self.table.setColumnWidth(1, 300)  # Path column
        self.table.setColumnWidth(2, 150)  # Date Modified column
        self.table.setColumnWidth(3, 100)  # Type column
        self.table.setColumnWidth(4, 100)  # Size column

        self.table.setSortingEnabled(False)

        layout.addWidget(self.table)

        # Move the status label to the bottom
        self.status_label = QLabel("Searching...")
        layout.addWidget(self.status_label)

        self.setLayout(layout)

        self.search_thread = None
        self.result_count = 0
        self.current_search_id = None

        # Connect input fields to search function
        self.name_input.returnPressed.connect(self.start_search_from_input)
        self.content_input.returnPressed.connect(self.start_search_from_input)

    def browse_directory(self):
        directory = QFileDialog.getExistingDirectory(self, "Select Directory")
        if directory:
            # Convert to OS-specific path
            directory = os.path.normpath(directory)
            self.path_input.setText(directory)
            self.start_search_from_input()

    def start_search(self, root_path: str, name_query: str, content_query: str):
        self.stop_current_search()
        self.table.setRowCount(0)
        self.table.clearContents()  # Clear all items from the table
        self.result_count = 0
        self.status_label.setText("Searching...")

        if not os.path.isdir(root_path):
            root_path = os.path.expanduser("~")

        self.current_search_id = str(uuid.uuid4())  # Generate a new search ID
        self.search_thread = SearchThread(
            root_path, name_query, content_query, self.current_search_id
        )
        self.search_thread.result_found.connect(self.add_result)
        self.search_thread.finished.connect(self.search_finished)
        self.search_thread.start()

        # Ensure the window is visible and in focus
        self.show()
        self.activateWindow()
        self.raise_()
        self.setFocus(Qt.FocusReason.OtherFocusReason)

    def stop_current_search(self):
        if self.search_thread and self.search_thread.isRunning():
            self.search_thread.stop()
            self.search_thread.wait()
            self.search_thread.deleteLater()
            self.search_thread = None

    def add_result(
        self,
        name: str,
        full_path: str,
        date_modified: str,
        file_type: str,
        size: str,
        search_id: str,
    ):
        if search_id != self.current_search_id:
            return  # Ignore results from old searches

        row = self.table.rowCount()
        self.table.insertRow(row)
        self.table.setItem(row, 0, QTableWidgetItem(name))
        self.table.setItem(row, 1, QTableWidgetItem(full_path))
        self.table.setItem(row, 2, QTableWidgetItem(date_modified))
        self.table.setItem(row, 3, QTableWidgetItem(file_type))
        self.table.setItem(row, 4, QTableWidgetItem(size))
        # Set the full path as item data for later use
        self.table.item(row, 0).setData(Qt.ItemDataRole.UserRole, full_path)

        # Set custom sort role data for the size column
        size_item = self.table.item(row, 4)
        size_value = int(size.split()[0]) if size else -1
        size_item.setData(Qt.ItemDataRole.UserRole, size_value)

        self.result_count += 1
        self.update_status_label()

    def update_status_label(self):
        self.status_label.setText(f"Found {self.result_count} results")

    def search_finished(self, search_id: str):
        if search_id != self.current_search_id:
            return  # Ignore finished signal from old searches

        self.status_label.setText(f"Search complete. Found {self.result_count} results")

    def navigate_to_item(self, row: int, _: int):
        path = self.table.item(row, 0).data(Qt.ItemDataRole.UserRole)
        file_explorer: any = self.parent()

        if os.path.isdir(path):
            file_explorer.navigation_manager.navigate_to(path)
        else:
            file_explorer.navigation_manager.navigate_to(os.path.dirname(path))

    def on_selection_changed(self):
        # Enable key press events when an item is selected
        self.setFocus()

    def keyPressEvent(self, event: QKeyEvent) -> None:
        if event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            selected_rows = self.table.selectionModel().selectedRows()
            if selected_rows:
                self.navigate_to_item(selected_rows[0].row(), 0)
        else:
            super().keyPressEvent(event)

    def position_window(self):
        file_explorer: any = self.parent()
        parent_geometry: QMainWindow = file_explorer.geometry()

        # Position the search window to the right of the parent window
        self.setGeometry(
            parent_geometry.right(),  # type: ignore
            parent_geometry.top(),  # type: ignore
            self.width(),
            parent_geometry.height(),  # type: ignore
        )

    def showEvent(self, event: QShowEvent) -> None:
        super().showEvent(event)
        self.position_window()
        self.raise_()

    def closeEvent(self, event: QCloseEvent) -> None:
        self.stop_current_search()
        super().closeEvent(event)

    def start_search_from_input(self):
        query = self.name_input.text()
        path = self.path_input.text()
        content = self.content_input.text()

        if path:
            self.start_search(path, query, content)

    def set_name_input(self, query: str):
        self.name_input.setText(query)

    def set_path_input(self, path: str, search: bool = True):
        # Convert to OS-specific path
        path = os.path.normpath(path)
        self.path_input.setText(path)
        if search:
            self.start_search_from_input()

    def set_content_input(self, content: str):
        self.content_input.setText(content)
