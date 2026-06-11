import sys
import os
os.environ["QT_QPA_PLATFORM"] = "offscreen"
from PyQt6.QtWidgets import QApplication
from ui_main import MainWindowUI
import time

app = QApplication(sys.argv)
window = MainWindowUI()
window.show()
print("UI loaded successfully.")
time.sleep(1)
