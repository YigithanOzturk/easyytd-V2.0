import os
import sys
import requests
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QComboBox,
    QFileDialog, QProgressBar, QMessageBox, QCheckBox, QDialog, QFormLayout,
    QDialogButtonBox, QToolButton, QListWidget, QListWidgetItem, QTextEdit, QMenuBar, QAction
)
from PyQt5.QtCore import Qt, QTimer, QSize, QUrl
from PyQt5.QtGui import QIcon, QPixmap, QCursor, QDesktopServices

from downloader import InfoFetchThread, DownloadThread, SUBTITLE_LANGS
from settings import load_settings, save_settings, load_history, save_history, clear_history, DEFAULT_SETTINGS
from utils import get_system_language

def resource_path(relative_path):
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)

class SettingsDialog(QDialog):
    def __init__(self, settings, format_list, quality_list, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Ayarlar")
        self.setModal(True)
        self.resize(400, 220)
        self.settings = settings.copy()
        layout = QFormLayout(self)

        self.dark_checkbox = QCheckBox("Dark Mode")
        self.dark_checkbox.setChecked(self.settings.get("dark_mode", False))
        layout.addRow("Tema:", self.dark_checkbox)

        self.format_combo = QComboBox()
        self.format_combo.addItems(format_list)
        if self.settings.get("default_format") in format_list:
            self.format_combo.setCurrentText(self.settings.get("default_format"))
        layout.addRow("Varsayılan Format:", self.format_combo)

        self.quality_combo = QComboBox()
        self.quality_combo.addItems(quality_list if quality_list else ["best"])
        if self.settings.get("default_quality") in quality_list:
            self.quality_combo.setCurrentText(self.settings.get("default_quality"))
        layout.addRow("Varsayılan Çözünürlük:", self.quality_combo)

        self.path_input = QLineEdit(self.settings.get("default_download_path", os.path.expanduser("~")))
        browse_btn = QPushButton("Gözat")
        browse_btn.clicked.connect(self.browse_path)
        path_layout = QHBoxLayout()
        path_layout.addWidget(self.path_input)
        path_layout.addWidget(browse_btn)
        layout.addRow("Varsayılan İndirme Yolu:", path_layout)

        self.sub_lang_combo = QComboBox()
        self.sub_lang_combo.addItems(list(SUBTITLE_LANGS.keys()))
        self.sub_lang_combo.setCurrentText(self.settings.get("default_sub_lang", "Otomatik"))
        layout.addRow("Varsayılan Altyazı Dili:", self.sub_lang_combo)

        buttons = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addRow(buttons)

    def browse_path(self):
        folder = QFileDialog.getExistingDirectory(self, "Kayıt klasörü seçin")
        if folder:
            self.path_input.setText(folder)

    def get_settings(self):
        return {
            "dark_mode": self.dark_checkbox.isChecked(),
            "default_format": self.format_combo.currentText(),
            "default_quality": self.quality_combo.currentText(),
            "default_download_path": self.path_input.text().strip() or os.path.expanduser("~"),
            "default_sub_lang": self.sub_lang_combo.currentText()
        }
 
class DownloaderApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("easyytd - YouTube Video İndirici")
        self.setWindowIcon(QIcon(resource_path("easyytd_logo.ico")))
        self.setMinimumSize(570, 600)
        self.settings = load_settings()
        self.history = load_history()
        self.last_formats = ['mp3', 'mp4', 'webm', 'mkv']
        self.last_qualities = ['1080p (?? MB) [mp4]', '720p (?? MB) [mp4]', 'best']
        self.init_ui()
        self.apply_settings()
        self.check_for_update()
        self.clipboard_auto_paste()
        self.setAcceptDrops(True)

    def init_ui(self):
        main_layout = QVBoxLayout(self)

        # Menü çubuğu
        self.menubar = QMenuBar(self)
        settings_menu = self.menubar.addMenu("Ayarlar")
        clear_history_action = QAction("Geçmişi Temizle", self)
        clear_history_action.triggered.connect(self.clear_history_clicked)
        settings_menu.addAction(clear_history_action)
        about_action = QAction("Hakkında", self)
        about_action.triggered.connect(self.show_about)
        settings_menu.addAction(about_action)
        main_layout.setMenuBar(self.menubar)

        title_layout = QHBoxLayout()
        label = QLabel("easyytd - YouTube Video İndirici")
        label.setStyleSheet("font-size: 20px; font-weight: bold;")
        label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        title_layout.addWidget(label)
        self.settings_btn = QToolButton()
        self.settings_btn.setIcon(QIcon(resource_path("easyytd_logo.ico")))
        self.settings_btn.setIconSize(QSize(28, 28))
        self.settings_btn.setToolTip("Ayarlar")
        self.settings_btn.clicked.connect(self.show_settings)
        title_layout.addStretch()
        title_layout.addWidget(self.settings_btn)
        main_layout.addLayout(title_layout)

        url_layout = QHBoxLayout()
        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("YouTube video URL’si giriniz...")
        self.url_input.setMinimumWidth(200)
        url_layout.addWidget(QLabel("URL:"))
        url_layout.addWidget(self.url_input)
        self.fetch_btn = QPushButton("ARA")
        self.fetch_btn.clicked.connect(self.fetch_video_info)
        url_layout.addWidget(self.fetch_btn)
        main_layout.addLayout(url_layout)

        self.supported_label = QLabel(
        "Desteklenen platformlar: YouTube, Vimeo, TikTok, Instagram, Facebook, Twitter ve çok daha fazlası! "
        '<a href="https://github.com/yt-dlp/yt-dlp/blob/master/supportedsites.md">[tam liste]</a>'
    )
        self.supported_label.setOpenExternalLinks(True)
        self.supported_label.setStyleSheet("color: #444; font-size: 12px; padding-bottom:5px;")
        main_layout.addWidget(self.supported_label)

        multi_links_layout = QHBoxLayout()
        self.multi_links_text = QTextEdit()
        self.multi_links_text.setPlaceholderText("Çoklu indirme için her satıra bir Youtube linki yapıştırın.")
        self.multi_links_text.setFixedHeight(60)
        multi_links_layout.addWidget(self.multi_links_text)
        self.batch_download_btn = QPushButton("Tümünü İndir")
        self.batch_download_btn.clicked.connect(self.start_batch_download)
        multi_links_layout.addWidget(self.batch_download_btn)
        main_layout.addLayout(multi_links_layout)

        self.video_info_box = QHBoxLayout()
        self.thumb_label = QLabel()
        self.thumb_label.setFixedSize(120, 68)
        self.thumb_label.setScaledContents(True)
        self.info_labels = QVBoxLayout()
        self.title_label = QLabel("Başlık: -")
        self.channel_label = QLabel("Kanal: -")
        self.duration_label = QLabel("Süre: -")
        self.title_label.setWordWrap(True)
        self.info_labels.addWidget(self.title_label)
        self.info_labels.addWidget(self.channel_label)
        self.info_labels.addWidget(self.duration_label)
        self.video_info_box.addWidget(self.thumb_label)
        self.video_info_box.addLayout(self.info_labels)
        main_layout.addLayout(self.video_info_box)

        select_layout = QHBoxLayout()
        select_layout.addWidget(QLabel("Format:"))
        self.format_combo = QComboBox()
        self.format_combo.addItems(self.last_formats)
        select_layout.addWidget(self.format_combo)
        select_layout.addWidget(QLabel("Çözünürlük:"))
        self.quality_combo = QComboBox()
        self.quality_combo.addItems(self.last_qualities)
        select_layout.addWidget(self.quality_combo)
        main_layout.addLayout(select_layout)

        type_layout = QHBoxLayout()
        type_layout.addWidget(QLabel("İndirme Türü:"))
        self.download_type_combo = QComboBox()
        self.download_type_combo.addItems([
            "Birleştir (Normal)",
            "Sadece Görüntü",
            "Sadece Ses",
            "Ayrı Ayrı (Ses + Video)"
        ])
        type_layout.addWidget(self.download_type_combo)
        main_layout.addLayout(type_layout)

        subtitle_row = QHBoxLayout()
        self.subtitle_checkbox = QCheckBox("Altyazı indir")
        self.subtitle_lang_combo = QComboBox()
        self.subtitle_lang_combo.addItems(list(SUBTITLE_LANGS.keys()))
        self.subtitle_lang_combo.setCurrentText(self.settings.get("default_sub_lang", "Otomatik"))
        subtitle_row.addWidget(self.subtitle_checkbox)
        subtitle_row.addWidget(self.subtitle_lang_combo)
        main_layout.addLayout(subtitle_row)

        self.playlist_checkbox = QCheckBox("Tüm oynatma listesini indir")
        self.playlist_checkbox.setChecked(False)
        main_layout.addWidget(self.playlist_checkbox)

        path_layout = QHBoxLayout()
        self.path_input = QLineEdit()
        self.path_input.setPlaceholderText("Kaydedilecek klasör seçin...")
        path_layout.addWidget(QLabel("Kayıt Yolu:"))
        path_layout.addWidget(self.path_input)
        self.browse_btn = QPushButton("Gözat")
        self.browse_btn.clicked.connect(self.select_path)
        path_layout.addWidget(self.browse_btn)
        main_layout.addLayout(path_layout)

        # --- Klip Aralığı Seçimi ---
        clip_row = QHBoxLayout()
        self.clip_checkbox = QCheckBox("Belirli aralığı indir")
        self.clip_start_input = QLineEdit()
        self.clip_start_input.setPlaceholderText("Başlangıç (ss:dd:sn)")
        self.clip_start_input.setFixedWidth(120)
        self.clip_end_input = QLineEdit()
        self.clip_end_input.setPlaceholderText("Bitiş (ss:dd:sn)")
        self.clip_end_input.setFixedWidth(120)
        clip_row.addWidget(self.clip_checkbox)
        clip_row.addWidget(self.clip_start_input)
        clip_row.addWidget(self.clip_end_input)
        main_layout.addLayout(clip_row)


        self.download_btn = QPushButton("İndir")
        self.download_btn.clicked.connect(self.start_download)
        main_layout.addWidget(self.download_btn)

        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        main_layout.addWidget(self.progress_bar)
        self.status_label = QLabel("")
        self.status_label.setStyleSheet("color: gray;")
        main_layout.addWidget(self.status_label)
        self.speed_label = QLabel("Hız: - | Kalan: -")  
        main_layout.addWidget(self.speed_label)



        history_label = QLabel("İndirme Geçmişi (son 10):")
        history_label.setStyleSheet("font-size: 13px; font-weight: bold; padding-top:8px;")
        main_layout.addWidget(history_label)
        self.history_list = QListWidget()
        self.history_list.setMaximumHeight(100)
        self.history_list.itemDoubleClicked.connect(self.open_history_file)
        main_layout.addWidget(self.history_list)
        self.refresh_history()

        github_row = QHBoxLayout()
        github_row.addStretch()
        self.github_logo = QLabel()
        try:
            github_pix = QPixmap()
            github_pix.loadFromData(requests.get("https://github.githubassets.com/images/modules/logos_page/GitHub-Mark.png").content)
            self.github_logo.setPixmap(github_pix.scaled(22, 22, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        except Exception:
            self.github_logo.setText("@YigithanOzturk")
        self.github_logo.setCursor(QCursor(Qt.PointingHandCursor))
        self.github_logo.mousePressEvent = self._open_github
        github_row.addWidget(self.github_logo)
        self.github_link = QLabel('<a href="https://github.com/YigithanOzturk">@YigithanOzturk</a>')
        self.github_link.setOpenExternalLinks(True)
        self.github_link.setStyleSheet("font-size: 13px; color: #0366d6; padding-left:5px;")
        github_row.addWidget(self.github_link)
        github_row.addSpacing(8)
        main_layout.addLayout(github_row)
        self.setLayout(main_layout)
 
    def _open_github(self, event):
        QDesktopServices.openUrl(QUrl("https://github.com/YigithanOzturk"))

    def apply_settings(self):
        s = self.settings
        if s.get("dark_mode", False):
            QApplication.instance().setStyleSheet("""
                QWidget { font-size: 14px; background: #191c22; color: #e7e7ef; }
                QLineEdit, QComboBox, QTextEdit { background: #23242a; color: #e7e7ef; border: 1px solid #444; }
                QLineEdit:focus, QComboBox:focus, QTextEdit:focus { border: 1.5px solid #74a9ff; background: #23243a; }
                QPushButton { background: #222d38; color: #e7e7ef; border-radius: 8px; padding: 7px 20px; font-weight: bold; }
                QProgressBar { background: #292c31; height: 18px; border-radius: 6px; }
            """)
        else:
            QApplication.instance().setStyleSheet("""
                QWidget { font-size: 14px; background: #f4f7fa; color: #111; }
                QLineEdit, QComboBox, QTextEdit { background: #fff; color: #111; border: 1px solid #bbb; }
                QLineEdit:focus, QComboBox:focus, QTextEdit:focus { border: 1.5px solid #3260a8; background: #f0f8ff; }
                QPushButton { background: #e7ebf2; color: #222; border-radius: 8px; padding: 7px 20px; font-weight: bold; }
                QProgressBar { background: #f1f1f1; height: 18px; border-radius: 6px; }
            """)
        self.format_combo.setCurrentText(s.get("default_format", "mp4"))
        self.quality_combo.setCurrentText(s.get("default_quality", "1080p (?? MB) [mp4]"))
        self.path_input.setText(s.get("default_download_path", os.path.expanduser("~")))
        self.subtitle_lang_combo.setCurrentText(s.get("default_sub_lang", "Otomatik"))

    def show_settings(self):
        dialog = SettingsDialog(
            self.settings,
            [self.format_combo.itemText(i) for i in range(self.format_combo.count())],
            [self.quality_combo.itemText(i) for i in range(self.quality_combo.count())],
            self)
        if dialog.exec_() == QDialog.Accepted:
            new_settings = dialog.get_settings()
            self.settings.update(new_settings)
            save_settings(self.settings)
            self.apply_settings()

    def select_path(self):
        folder = QFileDialog.getExistingDirectory(self, "Kayıt klasörü seçin")
        if folder:
            self.path_input.setText(folder)

    def fetch_video_info(self):
        url = self.url_input.text().strip()
        if not url:
            self.show_error("Lütfen bir YouTube video URL’si giriniz.")
            return
        self.status_label.setText("Video bilgisi alınıyor...")
        self.fetch_btn.setEnabled(False)
        QApplication.setOverrideCursor(Qt.WaitCursor)
        self.info_thread = InfoFetchThread(url)
        self.info_thread.info_ready.connect(self._on_video_info_ready)
        self.info_thread.error.connect(self._on_video_info_error)
        self.info_thread.finished.connect(lambda: QApplication.restoreOverrideCursor())
        self.info_thread.finished.connect(lambda: self.fetch_btn.setEnabled(True))
        self.info_timeout_timer = QTimer(self)
        self.info_timeout_timer.setSingleShot(True)
        self.info_timeout_timer.timeout.connect(self._on_info_timeout)
        self.info_timeout_timer.start(10000)
        self.info_thread.start()

    def _on_video_info_ready(self, info, formats, qualities):
        if hasattr(self, "info_timeout_timer"):
            self.info_timeout_timer.stop()
        self.show_video_info(info)
        self.status_label.setText("Video bilgisi yüklendi.")
        self.format_combo.blockSignals(True)
        self.quality_combo.blockSignals(True)
        self.format_combo.clear()
        self.format_combo.addItems(formats)
        self.quality_combo.clear()
        self.quality_combo.addItems(qualities)
        self.format_combo.blockSignals(False)
        self.quality_combo.blockSignals(False)
        self.format_combo.setCurrentText(self.settings.get("default_format", "mp4"))
        if self.settings.get("default_quality") in qualities:
            self.quality_combo.setCurrentText(self.settings.get("default_quality"))

    def _on_video_info_error(self, err):
        if hasattr(self, "info_timeout_timer"):
            self.info_timeout_timer.stop()
        self.show_video_info(None)
        self.status_label.setText(f"Video bilgisi alınamadı: {err}")

    def _on_info_timeout(self):
        self.status_label.setText("İşlem zaman aşımına uğradı, lütfen tekrar deneyin.")
        self.fetch_btn.setEnabled(True)
        QApplication.restoreOverrideCursor()
        try:
            self.info_thread.terminate()
        except Exception:
            pass

    def show_video_info(self, info):
        if not info:
            self.thumb_label.clear()
            self.title_label.setText("Başlık: -")
            self.channel_label.setText("Kanal: -")
            self.duration_label.setText("Süre: -")
            return
        thumb_url = info.get("thumbnail", "")
        if thumb_url:
            try:
                img = requests.get(thumb_url, timeout=5).content
                pix = QPixmap()
                pix.loadFromData(img)
                self.thumb_label.setPixmap(pix.scaled(120, 68, Qt.KeepAspectRatio))
            except Exception:
                self.thumb_label.clear()
        self.title_label.setText(f"Başlık: {info.get('title', '-')}")
        self.channel_label.setText(f"Kanal: {info.get('uploader', '-')}")
        dur = int(info.get('duration', 0))
        mins, secs = divmod(dur, 60)
        h, mins = divmod(mins, 60)
        duration_str = f"{h:02d}:{mins:02d}:{secs:02d}" if h else f"{mins:02d}:{secs:02d}"
        self.duration_label.setText(f"Süre: {duration_str}")

    def start_download(self):
        url = self.url_input.text().strip()
        path = self.path_input.text().strip()
        fmt = self.format_combo.currentText().lower()
        quality = self.quality_combo.currentText()
        is_playlist = self.playlist_checkbox.isChecked()
        download_type = self.download_type_combo.currentText()
        subtitle = self.subtitle_checkbox.isChecked()
        sub_lang = self.subtitle_lang_combo.currentText()
        clip_enabled = self.clip_checkbox.isChecked()
        clip_start = self.clip_start_input.text().strip()
        clip_end = self.clip_end_input.text().strip()

        if not url:
            self.show_error("Lütfen bir video URL’si giriniz.")
            return
        if not path or not os.path.isdir(path):
            self.show_error("Lütfen geçerli bir kayıt klasörü seçiniz.")
            return
        if not fmt or not quality:
            self.show_error("Lütfen format ve kalite seçiniz.")
            return

        self.status_label.setText("İndirme başlatılıyor...")
        self.speed_label.setText("Hız: - | Kalan: -")
        self.download_btn.setEnabled(False)
        self.progress_bar.setValue(0)

        self.dl_thread = DownloadThread(
            url, path, fmt, quality, is_playlist, download_type, subtitle, sub_lang,
            clip_enabled, clip_start, clip_end
        )
        self.dl_thread.progress.connect(self.progress_bar.setValue)
        self.dl_thread.done.connect(self.download_done)
        self.dl_thread.speed_eta.connect(self.update_speed_eta)  # <-- HIZ/KALAN SÜRE GÜNCELLEME
        self.dl_thread.start()

    def update_speed_eta(self, speed, eta):
        speed_str = f"{speed/1024/1024:.2f} MB/s" if speed else "-"
        if eta:
            m, s = divmod(eta, 60)
            eta_str = f"{m} dk {s} sn"
        else:
            eta_str = "-"
            self.speed_label.setText(f"Hız: {speed_str} | Kalan: {eta_str}")



    def start_batch_download(self):
        links = [line.strip() for line in self.multi_links_text.toPlainText().split('\n') if line.strip()]
        if not links:
            self.show_error("Çoklu indirme için en az bir Youtube linki girmelisiniz.")
            return
        self.status_label.setText("Toplu indirme başlatılıyor...")
        self.batch_queue = links
        self._process_next_in_queue()

    def _process_next_in_queue(self):
        if not hasattr(self, "batch_queue") or not self.batch_queue:
            self.status_label.setText("Tüm indirmeler tamamlandı.")
            return
        url = self.batch_queue.pop(0)
        self.url_input.setText(url)
        self.start_download()
        QTimer.singleShot(300, lambda: None)

    def download_done(self, message, file_path, video_title):
        self.status_label.setText(message)
        self.download_btn.setEnabled(True)
        if file_path:
            self.add_to_history(file_path)
            QMessageBox.information(self, "İndirme Bitti", f"'{video_title}' başarıyla indirildi!\n\n{file_path}")
        if hasattr(self, "batch_queue") and self.batch_queue:
            QTimer.singleShot(1000, self._process_next_in_queue)
        else:
            self.batch_queue = []

    def add_to_history(self, file_path):
        if ";" in file_path:
            for f in file_path.split(";"):
                f = f.strip()
                if f and os.path.exists(f):
                    self.history.insert(0, f)
        elif file_path and os.path.exists(file_path):
            self.history.insert(0, file_path)
        self.history = self.history[:10]
        save_history(self.history)
        self.refresh_history()

    def refresh_history(self):
        self.history_list.clear()
        for file_ in self.history:
            if not os.path.exists(file_):
                continue
            item = QListWidgetItem(os.path.basename(file_))
            item.setToolTip(file_)
            self.history_list.addItem(item)

    def open_history_file(self, item):
        file_path = item.toolTip()
        if os.path.exists(file_path):
            QDesktopServices.openUrl(QUrl.fromLocalFile(os.path.dirname(file_path)))

    def show_error(self, msg):
        QMessageBox.critical(self, "Hata", msg)


    # ----- YENİ EKSTRA FONKSİYONLAR -----

    def clear_history_clicked(self):
        clear_history()
        self.history = []
        self.refresh_history()
        QMessageBox.information(self, "Geçmiş Temizlendi", "İndirme geçmişi başarıyla temizlendi.")

    def show_about(self):
        QMessageBox.information(self, "Hakkında", "easyytd v1.0\nYouTube Video, Müzik ve Shorts İndirici\nYigithan Ozturk\nhttps://github.com/YigithanOzturk")

    def check_for_update(self):
        # Basit github sürüm kontrolü
        try:
            version_url = "https://raw.githubusercontent.com/YigithanOzturk/easyytd/main/VERSION"
            response = requests.get(version_url, timeout=3)
            if response.status_code == 200:
                latest_version = response.text.strip()
                local_version = "1.0"
                if local_version != latest_version:
                    QMessageBox.information(self, "Yeni Sürüm Mevcut", f"Yeni sürüm ({latest_version}) mevcut! Github'dan indiriniz.")
        except Exception:
            pass

    def clipboard_auto_paste(self):
        clipboard = QApplication.clipboard()
        text = clipboard.text()
        if "youtube.com" in text or "youtu.be" in text:
            self.url_input.setText(text)

    # Sürükle-bırak ile link ekleme
    def dragEnterEvent(self, event):
        if event.mimeData().hasText():
            event.acceptProposedAction()
    def dropEvent(self, event):
        text = event.mimeData().text()
        if "youtube.com" in text or "youtu.be" in text:
            self.url_input.setText(text)

 
 