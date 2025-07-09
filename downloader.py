import os
import time
import subprocess
from PyQt5.QtCore import QThread, pyqtSignal
import yt_dlp

SUBTITLE_LANGS = {
    "Otomatik": None,
    "Türkçe": ["tr"],
    "İngilizce": ["en"],
    "Tüm Diller": ["all"]
}

class InfoFetchThread(QThread):
    info_ready = pyqtSignal(object, list, list)
    error = pyqtSignal(str)
    def __init__(self, url):
        super().__init__()
        self.url = url
    def run(self):
        try:
            ydl_opts = {'quiet': True, 'skip_download': True, 'noplaylist': True}
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(self.url, download=False)
            if not info:
                self.error.emit("Video bilgisi alınamadı veya bağlantı desteklenmiyor.")
                return
            formats = set()
            qualities = []
            seen = set()
            for f in info.get('formats', []):
                if f.get('vcodec') != 'none':
                    ext = f.get('ext')
                    height = f.get('height')
                    filesize = f.get('filesize_approx') or f.get('filesize') or 0
                    if ext in ('mp4', 'webm', 'mkv') and height and (height, ext) not in seen:
                        mb = f"{round(filesize/1024/1024)} MB" if filesize else "?? MB"
                        qualities.append((height, ext, mb))
                        seen.add((height, ext))
                    formats.add(ext)
            formats.add('mp3')
            qualities = sorted(qualities, key=lambda x: int(x[0]), reverse=True)
            qualities_str = [f"{q[0]}p ({q[2]}) [{q[1]}]" for q in qualities]
            if not qualities_str:
                qualities_str = ["best"]
            formats = sorted(list(formats), key=lambda x: ('mp3', 'mp4', 'webm', 'mkv').index(x) if x in ('mp3', 'mp4', 'webm', 'mkv') else 99)
            self.info_ready.emit(info, formats, qualities_str)
        except Exception as e:
            self.error.emit(f"Video bilgisi alınamadı: {e}")

class DownloadThread(QThread):
    progress = pyqtSignal(int)
    done = pyqtSignal(str, str, str)
    speed_eta = pyqtSignal(float, int) 

    def __init__(
        self, url, download_path, fmt, quality, is_playlist, download_type, subtitle, sub_lang,
        clip_enabled=False, clip_start="", clip_end=""
    ):
        super().__init__()
        self.url = url
        self.download_path = download_path
        self.fmt = fmt
        self.quality = quality
        self.is_playlist = is_playlist
        self.download_type = download_type
        self.subtitle = subtitle
        self.sub_lang = sub_lang
        self.clip_enabled = clip_enabled
        self.clip_start = clip_start
        self.clip_end = clip_end

    def run(self):
        ydl_opts = {
            'outtmpl': os.path.join(self.download_path, '%(title)s.%(ext)s'),
            'progress_hooks': [self.my_hook],
            'ignoreerrors': True,
            'no-mtime': True
        }
        if not self.is_playlist:
            ydl_opts['noplaylist'] = True

        if self.subtitle:
            ydl_opts['writesubtitles'] = True
            ydl_opts['writeautomaticsub'] = True
            if SUBTITLE_LANGS.get(self.sub_lang):
                ydl_opts['subtitleslangs'] = SUBTITLE_LANGS[self.sub_lang]
            ydl_opts['subtitlesformat'] = 'vtt'

        try:
            import re
            m = re.match(r"(\d+)p.*\[(\w+)\]", self.quality)
            ext = self.fmt
            height = ""
            if m:
                height = m.group(1)
                ext = m.group(2)
            title = None
            downloaded_file = None
            info = None

            # --- Zorunlu H264/MP4/M4A formatı --- #
            def video_format_str():
                # mp4 uzantılı, H.264 (avc1) video, yükseklik eşleşirse
                if height:
                    return f'bestvideo[ext=mp4][vcodec^=avc1][height={height}]+bestaudio[ext=m4a]/best[ext=mp4]'
                else:
                    return 'bestvideo[ext=mp4][vcodec^=avc1]+bestaudio[ext=m4a]/best[ext=mp4]'

            def video_only_format_str():
                if height:
                    return f'bestvideo[ext=mp4][vcodec^=avc1][height={height}]'
                else:
                    return f'bestvideo[ext=mp4][vcodec^=avc1]'
            
            def audio_only_format_str():
                return 'bestaudio[ext=m4a]/bestaudio/best'

            if self.download_type == "Birleştir (Normal)":
                if self.fmt == 'mp3':
                    ydl_opts.update({
                        'format': 'bestaudio/best',
                        'postprocessors': [{
                            'key': 'FFmpegExtractAudio',
                            'preferredcodec': 'mp3',
                            'preferredquality': '192',
                        }],
                    })
                else:
                    ydl_opts['format'] = video_format_str()
                    ydl_opts['postprocessors'] = [{
                        'key': 'FFmpegVideoConvertor',
                        'preferedformat': 'mp4'
                    }]
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(self.url)
                    title = info.get("title", "indirilen")
                    for ext_ in ['mp3', 'mp4', 'webm', 'mkv']:
                        file_ = os.path.join(self.download_path, f"{title}.{ext_}")
                        if os.path.exists(file_):
                            downloaded_file = file_
                            break

                # FastStart
                if downloaded_file and downloaded_file.endswith(".mp4"):
                    fixed_file = downloaded_file.replace(".mp4", "_fixed.mp4")
                    try:
                        subprocess.run(
                            ["ffmpeg", "-y", "-i", downloaded_file, "-c", "copy", "-movflags", "faststart", fixed_file],
                            check=True,
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE
                        )
                        os.replace(fixed_file, downloaded_file)
                    except Exception as e:
                        print("FFmpeg ile remux hatası:", e)

            elif self.download_type == "Sadece Görüntü":
                ydl_opts['format'] = video_only_format_str()
                ydl_opts.pop('postprocessors', None)
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(self.url)
                    title = info.get("title", "indirilen")
                    video_file = None
                    for ext_ in ['mp4', 'webm', 'mkv']:
                        file_ = os.path.join(self.download_path, f"{title}.{ext_}")
                        if os.path.exists(file_):
                            video_file = file_
                            break

                if video_file and video_file.endswith(".mp4"):
                    fixed_file = video_file.replace(".mp4", "_fixed.mp4")
                    try:
                        subprocess.run(
                            ["ffmpeg", "-y", "-i", video_file, "-c", "copy", "-movflags", "faststart", fixed_file],
                            check=True,
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE
                        )
                        os.replace(fixed_file, video_file)
                    except Exception as e:
                        print("FFmpeg ile remux hatası:", e)
                downloaded_file = video_file

            elif self.download_type == "Sadece Ses":
                ydl_opts['format'] = audio_only_format_str()
                ydl_opts['postprocessors'] = [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '192',
                }]
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(self.url)
                    title = info.get("title", "indirilen")
                    file_ = os.path.join(self.download_path, f"{title}.mp3")
                    if os.path.exists(file_):
                        downloaded_file = file_

            elif self.download_type == "Ayrı Ayrı (Ses + Video)":
                # Video indir
                ydl_opts_vid = ydl_opts.copy()
                ydl_opts_vid['format'] = video_only_format_str()
                ydl_opts_vid['outtmpl'] = os.path.join(self.download_path, '%(title)s_video.%(ext)s')
                ydl_opts_vid.pop('postprocessors', None)
                with yt_dlp.YoutubeDL(ydl_opts_vid) as ydl:
                    info = ydl.extract_info(self.url)
                    title = info.get("title", "indirilen")
                    video_file = None
                    for ext_ in ['mp4', 'webm', 'mkv']:
                        file_ = os.path.join(self.download_path, f"{title}_video.{ext_}")
                        if os.path.exists(file_):
                            video_file = file_
                            break
                if video_file and video_file.endswith(".mp4"):
                    fixed_file = video_file.replace(".mp4", "_fixed.mp4")
                    try:
                        subprocess.run(
                            ["ffmpeg", "-y", "-i", video_file, "-c", "copy", "-movflags", "faststart", fixed_file],
                            check=True,
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE
                        )
                        os.replace(fixed_file, video_file)
                    except Exception as e:
                        print("FFmpeg ile remux hatası:", e)
                # Ses indir
                ydl_opts_audio = ydl_opts.copy()
                ydl_opts_audio['format'] = audio_only_format_str()
                ydl_opts_audio['outtmpl'] = os.path.join(self.download_path, '%(title)s_audio.%(ext)s')
                ydl_opts_audio.pop('postprocessors', None)
                with yt_dlp.YoutubeDL(ydl_opts_audio) as ydl:
                    info = ydl.extract_info(self.url)
                    title = info.get("title", "indirilen")
                    audio_file = None
                    for ext_ in ['mp3', 'm4a', 'webm']:
                        file_ = os.path.join(self.download_path, f"{title}_audio.{ext_}")
                        if os.path.exists(file_):
                            audio_file = file_
                            break
                downloaded_file = f"{video_file or ''} ; {audio_file or ''}"

            self.set_files_to_now(self.download_path, ext)
            output_file = downloaded_file

            # Klip özelliği
            if self.clip_enabled and output_file and os.path.exists(output_file):
                try:
                    base, ext_ = os.path.splitext(output_file)
                    clipped_file = f"{base}_clip{ext_}"
                    ffmpeg_cmd = [
                        "ffmpeg", "-y",
                        "-i", output_file,
                        "-ss", self.clip_start if self.clip_start else "00:00:00"
                    ]
                    if self.clip_end:
                        ffmpeg_cmd += ["-to", self.clip_end]
                    ffmpeg_cmd += ["-c", "copy", clipped_file]
                    subprocess.run(ffmpeg_cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                    downloaded_file = clipped_file
                except Exception as e:
                    print("Klip işlemi hatası:", e)

            self.done.emit("İndirme tamamlandı!", downloaded_file or "", (title or "İndirilen"))
        except Exception as e:
            self.done.emit(f"Hata: {str(e)}", "", "")

    def my_hook(self, d):
        if d.get('status') == 'downloading':
            percent = d.get('_percent_str', '0.0%').replace('%', '')
            try:
                self.progress.emit(int(float(percent)))
            except:
                self.progress.emit(0)
            speed = d.get('speed', 0)  # bytes/s
            eta = d.get('eta', 0)      # seconds
            self.speed_eta.emit(speed or 0, eta or 0)
        elif d.get('status') == 'finished':
            self.progress.emit(100)

    def set_files_to_now(self, folder, ext):
        now = time.time()
        files = [os.path.join(folder, f) for f in os.listdir(folder) if f.lower().endswith(ext)]
        if files:
            last_file = max(files, key=os.path.getctime)
            try:
                os.utime(last_file, (now, now))
            except Exception:
                pass
