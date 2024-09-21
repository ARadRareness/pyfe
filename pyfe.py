import os
import sys
from PySide6.QtWidgets import QApplication
from interface.file_explorer_ui import FileExplorerUI

if __name__ == "__main__":
    app = QApplication(sys.argv)
    base_dir = os.path.dirname(os.path.abspath(__file__))
    explorer = FileExplorerUI(base_dir)
    explorer.show()
    sys.exit(app.exec())
