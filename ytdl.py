import sys
import os
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                            QPushButton, QLineEdit, QLabel, QComboBox, QTextEdit, QFileDialog,
                            QProgressBar, QTabWidget, QMessageBox, QDesktopWidget)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QMutex, QTimer
from PyQt5.QtGui import QIcon, QClipboard, QTextCursor, QTextCharFormat, QColor
import yt_dlp
import shutil
import socket
from typing import List, Optional, Dict
from datetime import datetime
from enum import Enum
from collections import OrderedDict

# Enum for download modes
class DownloadMode(Enum):
    SINGLE = "single"
    LIST = "list"
    PLAYLIST = "playlist"

class DownloadWorker(QThread):
    progress = pyqtSignal(str)
    finished = pyqtSignal(bool)
    percentage = pyqtSignal(int)  # Sinyal untuk persentase progress bar
    _mutex = QMutex()
    
    def __init__(self, mode: DownloadMode, url_or_file: str, save_location: str, format_id: str = 'best'):
        super().__init__()
        self.mode = mode.value
        self.url_or_file = url_or_file
        self.save_location = save_location
        self.format_id = format_id
        self._running = True
        self.last_progress_message = ""
    
    def run(self):
        try:
            self._mutex.lock()
            if not self.check_network():
                self.progress.emit("No internet connection detected. Please check your network and try again.")
                self.finished.emit(False)
                return
                
            if self.mode == DownloadMode.SINGLE.value:
                self.download_single()
            elif self.mode == DownloadMode.LIST.value:
                self.download_list()
            elif self.mode == DownloadMode.PLAYLIST.value:
                self.download_playlist()
            else:
                raise ValueError("Invalid download mode selected.")
        except Exception as e:
            self.progress.emit(f"An unexpected error occurred: {str(e)}. Please try again or contact support.")
            self.finished.emit(False)
        finally:
            self._mutex.unlock()
    
    def stop(self):
        self._running = False
        self.progress.emit("Download stopped by user.")
    
    def check_network(self) -> bool:
        try:
            socket.create_connection(("8.8.8.8", 53), timeout=5)
            return True
        except (socket.gaierror, socket.timeout, OSError):
            return False
    
    def progress_hook(self, d):
        try:
            if not self._running:
                return
            if d['status'] == 'downloading':
                percent = d.get('_percent_str', '0%').strip('%')
                try:
                    self.percentage.emit(int(float(percent)))  # Kirim persentase ke progress bar
                except ValueError:
                    pass
            elif d['status'] == 'finished':
                self.progress.emit("Download completed successfully!")
                self.progress.emit(f"File saved to: {self.save_location}")
                self.percentage.emit(100)
        except KeyError as e:
            self.progress.emit(f"Error updating progress: Missing key '{str(e)}'. Please try again.")
    
    def download_single(self):
        try:
            is_audio_only = "audio_only" in self.format_id
            is_video_only = "video_only" in self.format_id
            base_format_id = self.format_id.replace("_video_only", "").replace("_audio_only", "") if self.format_id != "best" else self.format_id

            ydl_opts = {
                'outtmpl': os.path.join(self.save_location, '%(title)s.%(ext)s'),
                'socket_timeout': 30,
                'progress_hooks': [self.progress_hook],
                'noplaylist': True,
            }

            if is_audio_only:
                ydl_opts.update({
                    'format': 'bestaudio[ext=mp4]/bestaudio',
                    'postprocessors': [{
                        'key': 'FFmpegExtractAudio',
                        'preferredcodec': 'mp3',
                        'preferredquality': '192',
                    }],
                })
                self.progress.emit("Downloading audio only...")
            elif is_video_only:
                ydl_opts.update({
                    'format': base_format_id,
                    'merge_output_format': 'mp4',
                })
                self.progress.emit("Downloading video only (without audio)...")
            else:
                ydl_opts.update({
                    'format': 'bestvideo[ext=mp4]+bestaudio[ext=mp4]/best[ext=mp4]' if base_format_id == 'best' else f"{base_format_id}+bestaudio[ext=mp4]/best[ext=mp4]",
                    'merge_output_format': 'mp4',
                })
                self.progress.emit("Downloading video with audio...")

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(self.url_or_file, download=False)
                title = info.get('title', 'Unknown Title')
                self.progress.emit(f"Starting download for: '{title}'")
                ydl.download([self.url_or_file])
            self.finished.emit(True)
        except yt_dlp.utils.DownloadError as e:
            self.progress.emit(f"Download failed: {str(e)}. Please verify the URL or check your internet connection.")
            self.finished.emit(False)
        except PermissionError as e:
            self.progress.emit(f"Permission denied: {str(e)}. Please ensure you have write permissions for the save location.")
            self.finished.emit(False)
        except Exception as e:
            self.progress.emit(f"An error occurred during download: {str(e)}. Please try again.")
            self.finished.emit(False)
    
    def download_list(self):
        try:
            urls = self.read_url_file()
            if not urls:
                self.progress.emit("No valid URLs found in the file. Please check the file contents and try again.")
                self.finished.emit(False)
                return
                
            self.progress.emit(f"Found {len(urls)} URLs in the file. Starting batch download...")
            ydl_opts = {
                'format': 'bestvideo[ext=mp4]+bestaudio[ext=mp4]/best[ext=mp4]',
                'outtmpl': os.path.join(self.save_location, '%(title)s.%(ext)s'),
                'merge_output_format': 'mp4',
                'socket_timeout': 30,
                'progress_hooks': [self.progress_hook],
                'noplaylist': True,
            }
            
            success = True
            for i, url in enumerate(urls, 1):
                if not self._running:
                    break
                self.progress.emit(f"Downloading video {i} of {len(urls)}: {url}")
                try:
                    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                        ydl.download([url])
                except yt_dlp.utils.DownloadError as e:
                    self.progress.emit(f"Failed to download {url}: {str(e)}. Skipping to the next URL...")
                    success = False
            if success:
                self.progress.emit("All videos in the list downloaded successfully!")
            else:
                self.progress.emit("Some videos failed to download. Please check the log for details.")
            self.finished.emit(success)
        except Exception as e:
            self.progress.emit(f"Error during batch download: {str(e)}. Please try again.")
            self.finished.emit(False)
    
    def download_playlist(self):
        try:
            ydl_opts = {
                'format': 'bestvideo[ext=mp4]+bestaudio[ext=mp4]/best[ext=mp4]',
                'outtmpl': os.path.join(self.save_location, '%(playlist_title)s/%(title)s.%(ext)s'),
                'merge_output_format': 'mp4',
                'socket_timeout': 30,
                'progress_hooks': [self.progress_hook],
                'noplaylist': False,
            }
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(self.url_or_file, download=False)
                playlist_title = info.get('title', 'Unknown Playlist')
                self.progress.emit(f"Starting download for playlist: '{playlist_title}'")
                ydl.download([self.url_or_file])
            self.finished.emit(True)
        except yt_dlp.utils.DownloadError as e:
            self.progress.emit(f"Playlist download failed: {str(e)}. Please verify the URL or check your internet connection.")
            self.finished.emit(False)
        except PermissionError as e:
            self.progress.emit(f"Permission denied: {str(e)}. Please ensure you have write permissions for the save location.")
            self.finished.emit(False)
        except Exception as e:
            self.progress.emit(f"An error occurred during playlist download: {str(e)}. Please try again.")
            self.finished.emit(False)
    
    def read_url_file(self) -> List[str]:
        urls = []
        try:
            self.progress.emit(f"Reading URL file: '{self.url_or_file}'")
            with open(self.url_or_file, 'r', encoding='utf-8') as f:
                for line in f:
                    url = line.strip()
                    if url and self.is_valid_url(url):
                        urls.append(url)
            if not urls:
                self.progress.emit("No valid YouTube URLs found in the file.")
            return urls
        except FileNotFoundError:
            self.progress.emit(f"File not found: '{self.url_or_file}'. Please select a valid file.")
            return []
        except PermissionError:
            self.progress.emit(f"Permission denied for file: '{self.url_or_file}'. Please check file permissions.")
            return []
        except UnicodeDecodeError:
            self.progress.emit(f"Invalid encoding in file: '{self.url_or_file}'. Please use a UTF-8 encoded file.")
            return []
        except Exception as e:
            self.progress.emit(f"Error reading file: {str(e)}. Please try again.")
            return []
    
    def is_valid_url(self, url: str) -> bool:
        try:
            youtube_domains = ["youtube.com", "youtu.be"]
            return url.startswith(("http://", "https://")) and any(domain in url.lower() for domain in youtube_domains)
        except AttributeError:
            return False

class YTDLWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("YTDL v2.0")
        self.resize(900, 550)
        self.setMinimumSize(600, 400)
        self.setStyleSheet("QWidget { font-size: 14pt; }")
        self.update_window_title()
        
        try:
            self.setWindowIcon(QIcon('icon/ytdl.ico'))
        except Exception as e:
            print(f"Warning: Could not load icon: {str(e)}")
        
        self.worker = None
        self.format_cache = OrderedDict()
        self.max_cache_size = 50
        
        try:
            self.central_widget = QWidget()
            self.setCentralWidget(self.central_widget)
            self.layout = QVBoxLayout(self.central_widget)
            
            self.main_tabs = QTabWidget()
            self.layout.addWidget(self.main_tabs)
            
            self.download_tab = QWidget()
            self.download_layout = QVBoxLayout(self.download_tab)
            self.setup_download_tab()
            self.main_tabs.addTab(self.download_tab, "Download")
            
            self.about_tab = QWidget()
            self.about_layout = QVBoxLayout(self.about_tab)
            self.setup_about_tab()
            self.main_tabs.addTab(self.about_tab, "About")
            
            self.progress_label = QLabel("Progress")
            self.progress_label.setAlignment(Qt.AlignLeft)
            self.download_layout.addWidget(self.progress_label)
            self.progress_bar = QProgressBar()
            self.progress_bar.setMinimum(0)
            self.progress_bar.setMaximum(100)
            self.download_layout.addWidget(self.progress_bar)
            
            self.log_label = QLabel("Log")
            self.log_label.setAlignment(Qt.AlignLeft)
            self.download_layout.addWidget(self.log_label)
            self.log_output = QTextEdit()
            self.log_output.setReadOnly(True)
            self.download_layout.addWidget(self.log_output)
            
            self.check_dependencies()
            self.center_window()
            self.append_log("Welcome to YTDL v2.0! Ready to start your downloads.")
        except Exception as e:
            QMessageBox.critical(self, "Initialization Error", f"Failed to initialize application: {str(e)}")
            sys.exit(1)
    
    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.update_window_title()
    
    def update_window_title(self):
        width = self.width()
        height = self.height()
        self.setWindowTitle(f"YTDL v2.0 - {width}x{height}")
    
    def center_window(self):
        screen = QDesktopWidget().screenGeometry()
        size = self.geometry()
        self.move((screen.width() - size.width()) // 2, (screen.height() - size.height()) // 2)
    
    def closeEvent(self, event):
        if self.worker and self.worker.isRunning():
            self.worker.stop()
            self.worker.wait()
        self.append_log("Application closed. Thank you for using YTDL!")
        event.accept()
    
    def check_dependencies(self):
        try:
            if not shutil.which("ffmpeg"):
                self.append_log("FFmpeg is not installed. Please install FFmpeg to enable downloading.")
                self.single_download_btn.setEnabled(False)
                self.list_download_btn.setEnabled(False)
                self.playlist_download_btn.setEnabled(False)
        except Exception as e:
            self.append_log(f"Error checking dependencies: {str(e)}. Please ensure FFmpeg is installed correctly.")
    
    def setup_download_tab(self):
        self.download_sub_tabs = QTabWidget()
        self.download_layout.addWidget(self.download_sub_tabs)
        
        self.single_tab = QWidget()
        self.single_layout = QVBoxLayout(self.single_tab)
        self.setup_single_tab()
        self.download_sub_tabs.addTab(self.single_tab, "Single URL")
        
        self.list_tab = QWidget()
        self.list_layout = QVBoxLayout(self.list_tab)
        self.setup_list_tab()
        self.download_sub_tabs.addTab(self.list_tab, "URL List")
        
        self.playlist_tab = QWidget()
        self.playlist_layout = QVBoxLayout(self.playlist_tab)
        self.setup_playlist_tab()
        self.download_sub_tabs.addTab(self.playlist_tab, "Playlist")
    
    def setup_single_tab(self):
        url_layout = QHBoxLayout()
        url_layout.addWidget(QLabel("YouTube URL:"))
        self.single_url_input = QLineEdit()
        self.single_url_input.textChanged.connect(self.validate_url)
        url_layout.addWidget(self.single_url_input)
        self.single_paste_btn = QPushButton("Paste URL")
        self.single_paste_btn.clicked.connect(lambda: self.paste_url(self.single_url_input))
        url_layout.addWidget(self.single_paste_btn)
        self.single_layout.addLayout(url_layout)
        
        save_layout = QHBoxLayout()
        save_layout.addWidget(QLabel("Save Location:"))
        self.single_save_input = QLineEdit()
        self.single_browse_btn = QPushButton("Browse")
        self.single_browse_btn.clicked.connect(lambda: self.browse_location(self.single_save_input))
        save_layout.addWidget(self.single_save_input)
        save_layout.addWidget(self.single_browse_btn)
        self.single_layout.addLayout(save_layout)
        
        format_layout = QHBoxLayout()
        format_layout.addWidget(QLabel("Format:"))
        self.format_combo = QComboBox()
        self.format_combo.addItem("Video + Audio (Best Quality)", "best")
        self.get_formats_btn = QPushButton("Get Formats")
        self.get_formats_btn.clicked.connect(self.get_formats)
        format_layout.addWidget(self.format_combo)
        format_layout.addWidget(self.get_formats_btn)
        self.single_layout.addLayout(format_layout)
        
        self.single_download_btn = QPushButton("Download")
        self.single_download_btn.clicked.connect(self.start_download_single)
        self.single_layout.addWidget(self.single_download_btn)
    
    def setup_list_tab(self):
        file_layout = QHBoxLayout()
        file_layout.addWidget(QLabel("URL File:"))
        self.list_file_input = QLineEdit()
        self.list_browse_file_btn = QPushButton("Browse")
        self.list_browse_file_btn.clicked.connect(lambda: self.browse_file(self.list_file_input))
        file_layout.addWidget(self.list_file_input)
        file_layout.addWidget(self.list_browse_file_btn)
        self.list_layout.addLayout(file_layout)
        
        save_layout = QHBoxLayout()
        save_layout.addWidget(QLabel("Save Location:"))
        self.list_save_input = QLineEdit()
        self.list_browse_btn = QPushButton("Browse")
        self.list_browse_btn.clicked.connect(lambda: self.browse_location(self.list_save_input))
        save_layout.addWidget(self.list_save_input)
        save_layout.addWidget(self.list_browse_btn)
        self.list_layout.addLayout(save_layout)
        
        self.list_download_btn = QPushButton("Download")
        self.list_download_btn.clicked.connect(self.start_download_list)
        self.list_layout.addWidget(self.list_download_btn)
    
    def setup_playlist_tab(self):
        url_layout = QHBoxLayout()
        url_layout.addWidget(QLabel("Playlist URL:"))
        self.playlist_url_input = QLineEdit()
        self.playlist_url_input.textChanged.connect(self.validate_url)
        url_layout.addWidget(self.playlist_url_input)
        self.playlist_paste_btn = QPushButton("Paste URL")
        self.playlist_paste_btn.clicked.connect(lambda: self.paste_url(self.playlist_url_input))
        url_layout.addWidget(self.playlist_paste_btn)
        self.playlist_layout.addLayout(url_layout)
        
        save_layout = QHBoxLayout()
        save_layout.addWidget(QLabel("Save Location:"))
        self.playlist_save_input = QLineEdit()
        self.playlist_browse_btn = QPushButton("Browse")
        self.playlist_browse_btn.clicked.connect(lambda: self.browse_location(self.playlist_save_input))
        save_layout.addWidget(self.playlist_save_input)
        save_layout.addWidget(self.playlist_browse_btn)
        self.playlist_layout.addLayout(save_layout)
        
        self.playlist_download_btn = QPushButton("Download")
        self.playlist_download_btn.clicked.connect(self.start_download_playlist)
        self.playlist_layout.addWidget(self.playlist_download_btn)
    
    def setup_about_tab(self):
        about_text = QTextEdit()
        about_text.setReadOnly(True)
        about_text.setText("""
        YouTube Video Downloader v2.0
        
        Created by: Rofi (Fixploit03)
        GitHub: https://github.com/fixploit03/ytdl
        
        This application allows you to download YouTube videos in various modes:
        - Single URL: Download individual videos with customizable format options.
        - URL List: Download multiple videos from a text file.
        - Playlist: Download entire YouTube playlists.
        
        Requirements:
        - Python 3.x
        - PyQt5
        - yt-dlp
        - FFmpeg
        
        Support the Developer:
        If you find this tool useful, consider supporting me:
        - Donation: https://saweria.co/fixploit03
        
        Thank you for using YTDL!
        """)
        self.about_layout.addWidget(about_text)
    
    def paste_url(self, input_field: QLineEdit):
        try:
            clipboard = QApplication.clipboard()
            url = clipboard.text().strip()
            if url:
                input_field.setText(url)
                self.append_log(f"Pasted URL from clipboard: '{url}'")
            else:
                self.append_log("Clipboard is empty. Please copy a URL and try again.")
        except Exception as e:
            self.append_log(f"Error pasting URL: {str(e)}. Please try again.")
    
    def browse_location(self, input_field: QLineEdit):
        try:
            folder = QFileDialog.getExistingDirectory(self, "Select Save Location")
            if folder:
                input_field.setText(folder)
                self.append_log(f"Selected save location: '{folder}'")
            else:
                self.append_log("No save location selected.")
        except Exception as e:
            self.append_log(f"Error selecting save location: {str(e)}. Please try again.")
    
    def browse_file(self, input_field: QLineEdit):
        try:
            file = QFileDialog.getOpenFileName(self, "Select URL File", "", "Text Files (*.txt)")[0]
            if file:
                input_field.setText(file)
                self.append_log(f"Selected URL file: '{file}'")
            else:
                self.append_log("No URL file selected.")
        except Exception as e:
            self.append_log(f"Error selecting file: {str(e)}. Please try again.")
    
    def get_formats(self):
        try:
            url = self.single_url_input.text().strip()
            if not self.is_valid_url(url):
                self.append_log("Invalid YouTube URL. Please enter a valid URL to fetch formats.")
                return
                
            if url in self.format_cache:
                self._populate_format_combo(self.format_cache[url])
                self.append_log(f"Loaded formats from cache for: '{url}'")
                return
                
            self.append_log(f"Fetching available formats for: '{url}'...")
            ydl_opts = {'quiet': True, 'no_warnings': True}
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                formats = info.get('formats', [])
                if len(self.format_cache) >= self.max_cache_size:
                    self.format_cache.popitem(last=False)
                self.format_cache[url] = formats
                self._populate_format_combo(formats)
        except yt_dlp.utils.DownloadError as e:
            self.append_log(f"Failed to fetch formats: {str(e)}. Please check the URL or your internet connection.")
        except Exception as e:
            self.append_log(f"Error fetching formats: {str(e)}. Please try again.")
    
    def _populate_format_combo(self, formats: List[Dict]):
        self.format_combo.clear()
        self.format_combo.addItem("Video + Audio (Best Quality)", "best")
        
        resolution_dict: Dict[str, Dict[str, Optional[int]]] = {}
        for f in formats:
            if f.get('ext') == 'mp4' and f.get('vcodec') != 'none':
                resolution = f.get('height')
                filesize = f.get('filesize')
                if resolution is not None:
                    res_str = f"{resolution}p"
                    format_id = f.get('format_id')
                    filesize = filesize if filesize is not None else 0
                    if res_str not in resolution_dict or filesize > (resolution_dict[res_str]['filesize'] or 0):
                        resolution_dict[res_str] = {'format_id': format_id, 'filesize': filesize}
        
        video_audio_formats = []
        video_only_formats = []
        
        for res in sorted(resolution_dict.keys(), key=lambda x: int(x[:-1]), reverse=True):
            format_id = resolution_dict[res]['format_id']
            video_audio_formats.append((f"Video + Audio ({res})", format_id))
            video_only_formats.append((f"Video Only ({res})", f"{format_id}_video_only"))
        
        for label, format_id in video_audio_formats:
            self.format_combo.addItem(label, format_id)
        for label, format_id in video_only_formats:
            self.format_combo.addItem(label, format_id)
        
        self.format_combo.addItem("Audio Only (Best Quality)", "bestaudio_audio_only")
        total_formats = self.format_combo.count()
        self.append_log(f"Successfully loaded {total_formats} format options.")
    
    def is_valid_url(self, url: str) -> bool:
        try:
            youtube_domains = ["youtube.com", "youtu.be"]
            return url.startswith(("http://", "https://")) and any(domain in url.lower() for domain in youtube_domains)
        except AttributeError:
            self.append_log("URL validation error: Invalid URL format. Please enter a valid URL.")
            return False
    
    def validate_url(self, text: str):
        if not self.is_valid_url(text):
            self.single_url_input.setStyleSheet("border: 1px solid red;" if self.single_url_input.text() == text else "")
            self.playlist_url_input.setStyleSheet("border: 1px solid red;" if self.playlist_url_input.text() == text else "")
            self.single_download_btn.setEnabled(False)
            self.playlist_download_btn.setEnabled(False)
        else:
            self.single_url_input.setStyleSheet("")
            self.playlist_url_input.setStyleSheet("")
            self.single_download_btn.setEnabled(True)
            self.playlist_download_btn.setEnabled(True)
    
    def start_download(self, mode: DownloadMode, url_or_file: str, save_location: str, button: QPushButton):
        try:
            if self.worker and self.worker.isRunning():
                self.append_log("A download is already in progress. Please wait or stop the current download.")
                return
                
            if mode == DownloadMode.SINGLE and not self.is_valid_url(url_or_file):
                self.append_log("Invalid YouTube URL. Please enter a valid URL to start the download.")
                return
            if mode == DownloadMode.LIST and (not url_or_file or not os.path.isfile(url_or_file)):
                self.append_log("Invalid URL file. Please select a valid file to start the batch download.")
                return
            if mode == DownloadMode.PLAYLIST and not self.is_valid_url(url_or_file):
                self.append_log("Invalid playlist URL. Please enter a valid URL to start the download.")
                return
            if not save_location or not os.path.isdir(save_location):
                self.append_log("Invalid save location. Please select a valid directory before starting the download.")
                return
                
            format_id = self.format_combo.currentData() if mode == DownloadMode.SINGLE else "best"
            format_text = self.format_combo.currentText() if mode == DownloadMode.SINGLE else "Best Quality"
            self.append_log(f"Starting {mode.value} download.... Format: {format_text}")
            
            button.setEnabled(False)
            self.progress_bar.setValue(0)
            self.worker = DownloadWorker(mode, url_or_file, save_location, format_id)
            self.worker.progress.connect(self.update_progress)
            self.worker.percentage.connect(self.update_progress_bar)
            self.worker.finished.connect(lambda success: self.download_finished(success, button))
            self.worker.start()
        except Exception as e:
            self.append_log(f"Error starting download: {str(e)}. Please try again.")
    
    def start_download_single(self):
        self.start_download(DownloadMode.SINGLE, self.single_url_input.text().strip(), 
                          self.single_save_input.text().strip(), self.single_download_btn)
    
    def start_download_list(self):
        self.start_download(DownloadMode.LIST, self.list_file_input.text().strip(), 
                          self.list_save_input.text().strip(), self.list_download_btn)
    
    def start_download_playlist(self):
        self.start_download(DownloadMode.PLAYLIST, self.playlist_url_input.text().strip(), 
                          self.playlist_save_input.text().strip(), self.playlist_download_btn)
    
    def append_log(self, message: str):
        try:
            current_time = datetime.now().strftime("%H:%M:%S")
            log_message = f"[{current_time}] {message}"
            format = QTextCharFormat()
            format.setForeground(QColor("black"))
            cursor = self.log_output.textCursor()
            cursor.movePosition(QTextCursor.End)
            self.log_output.setTextCursor(cursor)
            self.log_output.setCurrentCharFormat(format)
            QTimer.singleShot(0, lambda: self.log_output.append(log_message))
            QTimer.singleShot(0, lambda: self.log_output.verticalScrollBar().setValue(self.log_output.verticalScrollBar().maximum()))
        except Exception as e:
            print(f"Warning: Failed to append log: {str(e)}")
    
    def update_progress(self, message: str):
        try:
            if "Download completed successfully!" in message:
                self.append_log(message)
            elif "Downloading:" not in message:
                self.append_log(message)
        except Exception as e:
            self.append_log(f"Unexpected error updating progress: {str(e)}. Please try again.")
    
    def update_progress_bar(self, percent: int):
        self.progress_bar.setValue(percent)
    
    def download_finished(self, success: bool, button: QPushButton):
        try:
            button.setEnabled(True)
            if success:
                self.append_log("Download operation completed successfully!")
            else:
                self.append_log("Download operation failed. Please check the log for details.")
                self.progress_bar.setValue(0)
            self.worker = None
        except Exception as e:
            self.append_log(f"Error handling download completion: {str(e)}. Please try again.")

if __name__ == '__main__':
    try:
        app = QApplication(sys.argv)
        window = YTDLWindow()
        window.show()
        sys.exit(app.exec_())
    except Exception as e:
        print(f"Critical error: {str(e)}")
        sys.exit(1)
