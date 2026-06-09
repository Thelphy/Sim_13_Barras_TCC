import sys
from PyQt6.QtWidgets import QApplication
from ui_main import MainWindowUI
import time

app = QApplication(sys.argv)
window = MainWindowUI()
window.show()
print("UI loaded successfully.")
time.sleep(1)
