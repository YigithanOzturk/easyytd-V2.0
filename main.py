from PyQt5.QtWidgets import QApplication
from gui import DownloaderApp
import sys

def main():
    app = QApplication(sys.argv)
    win = DownloaderApp()
    win.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
