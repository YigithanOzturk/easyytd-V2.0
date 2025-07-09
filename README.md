# easyytd

**Multi-Platform Video & Music Downloader**  
YouTube, TikTok, Twitter, Facebook, Instagram & more!

---

## 🚀 Quick Start

- **[⬇️ Download easyytd.exe](https://github.com/YigithanOzturk/easyytd/releases/latest)**
- No installation needed. Just run the `.exe` on Windows.
- [Download FFmpeg](https://ffmpeg.org/download.html) and copy all three exe files from the zip into the same folder as easyytd.exe:

    - `ffmpeg.exe`
    - `ffplay.exe`
    - `ffprobe.exe`

(You’ll find them in the FFmpeg zip archive.)

## Features

- Download from YouTube, TikTok, Twitter, Instagram, Facebook, and more!
- Batch download (multiple URLs)
- Download audio/video or both
- Choose quality & format (mp3, mp4, webm, mkv)
- Download specific time ranges (clips)
- Download subtitles (multi-language)
- Fast and lightweight, no installation required
- Dark & light theme
- Download history

## Run from Source

```sh

pip install -r requirements.txt
python main.py


# Build EXE (with PyInstaller)

Install PyInstaller:

pip install pyinstaller

Create EXE:

pyinstaller --onefile --windowed --icon=easyytd_logo.ico --name=easyytd main.py

Output will be in the dist/ folder.

Copy ffmpeg.exe, ffplay.exe, and ffprobe.exe from FFmpeg’s zip into the same folder as your EXE.

# easyytd

---

## Çoklu Platform Video & Müzik İndirici

YouTube, TikTok, Twitter, Facebook, Instagram ve daha fazlası!

---

### 🚀 Hızlı Başlangıç

- **[⬇️ easyytd.exe İndir](https://github.com/YigithanOzturk/easyytd/releases/latest)**
- Kurulum gerekmez. Windows için `.exe` dosyasını çalıştırın.
- [FFmpeg indir](https://ffmpeg.org/download.html) ve `easyytd.exe` ile aynı klasöre **şu üç dosyayı ekleyin**:
    - `ffmpeg.exe`
    - `ffplay.exe`
    - `ffprobe.exe`
  (FFmpeg’in .zip arşivinin içindedir.)

---

### Özellikler

- YouTube, TikTok, Twitter, Instagram, Facebook ve daha fazlasından indirme
- Toplu indirme (birden fazla URL)
- Video/ses veya ikisini indir
- Kalite & format seçimi (mp3, mp4, webm, mkv)
- Belirli zaman aralığı (klip) indir
- Altyazı indirme (çoklu dil)
- Hızlı ve hafif, kurulum gerekmez
- Koyu & açık tema
- İndirme geçmişi

---

### Koddan Çalıştırmak İçin

pip install -r requirements.txt
python main.py

# Exe Oluşturmak (PyInstaller ile)

PyInstaller kurulumu:

pip install pyinstaller

exe oluşturmak için:

pyinstaller --onefile --windowed --icon=easyytd_logo.ico --name=easyytd main.py

Çıktı dist/ klasöründe main.exe veya belirlediğin isimde oluşacaktır.

FFmpeg’den çıkan ffmpeg.exe, ffplay.exe, ffprobe.exe dosyalarını da aynı klasöre ekle.

```sh