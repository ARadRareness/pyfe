from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
)
from PySide6.QtCore import QDir


class HistoryWindow(QWidget):
    def __init__(self, parent):
        super().__init__()
        self.parent = parent
        self.setWindowTitle("History Explorer")
        self.setGeometry(200, 200, 600, 400)

        layout = QVBoxLayout()
        self.table = QTableWidget()
        self.table.setColumnCount(2)
        self.table.setHorizontalHeaderLabels(["Directory", "Last Visited"])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(
            1, QHeaderView.ResizeToContents
        )
        self.table.verticalHeader().setVisible(False)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.cellDoubleClicked.connect(self.navigate_to_directory)

        layout.addWidget(self.table)
        self.setLayout(layout)

        self.update_history()

    def update_history(self):
        history = self.parent.navigation_manager.get_history()
        self.table.setRowCount(len(history))
        for row, (path, timestamp) in enumerate(history):
            self.table.setItem(row, 0, QTableWidgetItem(path))
            self.table.setItem(
                row, 1, QTableWidgetItem(timestamp.toString("yyyy-MM-dd HH:mm:ss"))
            )

    def navigate_to_directory(self, row, column):
        if column == 0:
            path = self.table.item(row, 0).text()
            if QDir(path).exists():
                self.parent.navigation_manager.navigate_to(path)
            else:
                from PySide6.QtWidgets import QMessageBox

                QMessageBox.warning(
                    self,
                    "Directory Not Found",
                    f"The directory '{path}' no longer exists.",
                )

    def position_window(self):
        parent_geometry = self.parent.geometry()
        self.setGeometry(
            parent_geometry.right(),
            parent_geometry.top(),
            self.width(),
            parent_geometry.height(),
        )

    def showEvent(self, event):
        super().showEvent(event)
        self.update_history()
        self.position_window()
