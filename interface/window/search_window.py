from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QLabel,
    QAbstractItemView,
)
from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtWidgets import QMainWindow
import os

from PySide6.QtGui import QShowEvent, QCloseEvent, QKeyEvent


class SearchThread(QThread):
    result_found = Signal(str, str)
    finished = Signal()

    def __init__(self, root_path: str, query: str):
        super().__init__()
        self.root_path = root_path
        self.include_terms, self.exclude_terms = self.parse_query(query)
        self.stop_flag = False

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
        for root, dirs, files in os.walk(self.root_path):
            if self.stop_flag:
                break
            for name in dirs + files:
                if self.stop_flag:
                    break
                if self.match_query(name):
                    full_path = os.path.join(root, name)
                    self.result_found.emit(name, full_path)
        self.finished.emit()

    def stop(self):
        self.stop_flag = True


class SearchWindow(QWidget):
    def __init__(self, parent: QMainWindow):
        super().__init__(parent)
        self.setWindowTitle("Search Results")
        self.setGeometry(200, 200, 600, 400)
        self.setWindowFlags(Qt.WindowType.Window)

        layout = QVBoxLayout()
        self.status_label = QLabel("Searching...")
        layout.addWidget(self.status_label)

        self.table = QTableWidget()
        self.table.setColumnCount(2)
        self.table.setHorizontalHeaderLabels(["Name", "Path"])
        self.table.horizontalHeader().setSectionResizeMode(
            0, QHeaderView.ResizeMode.Stretch
        )
        self.table.horizontalHeader().setSectionResizeMode(
            1, QHeaderView.ResizeMode.Stretch
        )
        self.table.verticalHeader().setVisible(False)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.cellDoubleClicked.connect(self.navigate_to_item)
        self.table.itemSelectionChanged.connect(self.on_selection_changed)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)

        layout.addWidget(self.table)
        self.setLayout(layout)

        self.search_thread = None
        self.result_count = 0

    def start_search(self, root_path: str, query: str):
        self.stop_current_search()
        self.table.setRowCount(0)
        self.result_count = 0
        self.status_label.setText("Searching...")
        self.search_thread = SearchThread(root_path, query)
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

    def add_result(self, name: str, path: str):
        row = self.table.rowCount()
        self.table.insertRow(row)
        self.table.setItem(row, 0, QTableWidgetItem(name))

        # Show only the directory path, not the full path
        dir_path = os.path.dirname(path)
        self.table.setItem(row, 1, QTableWidgetItem(dir_path))

        self.result_count += 1
        self.update_status_label()

    def update_status_label(self):
        self.status_label.setText(f"Found {self.result_count} results")

    def search_finished(self):
        self.status_label.setText(f"Search complete. Found {self.result_count} results")

    def navigate_to_item(self, row: int, _: int):
        path = self.table.item(row, 1).text()
        file_explorer: any = self.parent()

        if os.path.isdir(path):
            file_explorer.navigation_manager.navigate_to(path)
        else:
            parent_dir = os.path.dirname(path)
            file_explorer.navigation_manager.navigate_to(parent_dir)

    def on_selection_changed(self):
        # Enable key press events when an item is selected
        self.setFocus()

    def keyPressEvent(self, event: QKeyEvent) -> None:
        if event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            selected_rows = self.table.selectionModel().selectedRows()
            if selected_rows:
                self.navigate_to_item(selected_rows[0].row(), 0)
            else:
                print("NO ROW SELECTED")
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
