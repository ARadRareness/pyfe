import os
from PySide6.QtWidgets import QHBoxLayout, QPushButton, QLineEdit, QCompleter
from PySide6.QtGui import QIcon, QPixmap
from PySide6.QtCore import QSize, Qt, QObject, QEvent, Signal


class AddressBar(QLineEdit):
    def __init__(self, parent=None):
        super().__init__(parent)


class ToolbarManager:
    def __init__(self, parent, base_dir, file_system_model):
        self.parent = parent
        self.base_dir = base_dir
        self.file_system_model = file_system_model  # Add this line
        self.back_btn = QPushButton()
        self.forward_btn = QPushButton()
        self.up_btn = QPushButton()
        self.refresh_btn = QPushButton()
        self.address_bar = AddressBar()
        self.search_bar = QLineEdit()

    def create_toolbar(self):
        toolbar = QHBoxLayout()
        self.setup_buttons()
        self.setup_address_bar()
        self.setup_search_bar()

        toolbar.addWidget(self.back_btn)
        toolbar.addWidget(self.forward_btn)
        toolbar.addWidget(self.up_btn)
        toolbar.addWidget(self.refresh_btn)
        toolbar.addWidget(self.address_bar)
        toolbar.addWidget(self.search_bar)

        return toolbar

    def setup_buttons(self):
        self.set_button_icon(self.back_btn, "back.png")
        self.set_button_icon(self.forward_btn, "forward.png")
        self.set_button_icon(self.up_btn, "up.png")
        self.set_button_icon(self.refresh_btn, "refresh.png")

    def setup_address_bar(self):
        self.address_bar = AddressBar()
        self.address_bar.returnPressed.connect(self.parent.change_directory)

        # completer = QCompleter()
        # completer.setModel(self.file_system_model)
        # completer.setCompletionMode(
        #    QCompleter.CompletionMode.InlineCompletion
        # )  # Change this line
        # completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        # completer.setFilterMode(Qt.MatchContains)  # Add this line
        # completer.setMaxVisibleItems(10)  # Add this line
        # self.address_bar.setCompleter(completer)

    def setup_search_bar(self):
        self.search_bar.setPlaceholderText("Search")
        self.search_bar.returnPressed.connect(self.parent.search_files)

    def set_button_icon(self, button, icon_name):
        icon_path = os.path.join(self.base_dir, "icons", icon_name)
        icon = QIcon(QPixmap(icon_path))
        button.setIcon(icon)
        button.setIconSize(QSize(16, 16))
        button.setFixedSize(24, 24)

    def connect_signals(self, navigation_manager):
        self.back_btn.clicked.connect(navigation_manager.go_back)
        self.forward_btn.clicked.connect(navigation_manager.go_forward)
        self.up_btn.clicked.connect(navigation_manager.go_up)
        self.refresh_btn.clicked.connect(self.parent.update_view)
        self.address_bar.returnPressed.connect(self.parent.change_directory)
        self.search_bar.returnPressed.connect(self.parent.search_files)

    def update_address_bar(self, path):
        self.address_bar.setText(path)

    def get_search_text(self):
        return self.search_bar.text()

    def clear_search_bar(self):
        self.search_bar.clear()

    def update_navigation_buttons(self, can_go_back, can_go_forward):
        self.back_btn.setEnabled(can_go_back)
        self.forward_btn.setEnabled(can_go_forward)

    def update_up_button(self, can_go_up):
        self.up_btn.setEnabled(can_go_up)
