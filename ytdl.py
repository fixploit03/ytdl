import yt_dlp
import os
import sys
import platform
from tabulate import tabulate
from typing import List, Optional
import shutil
import time
import socket

# Banner
banner = """
============================================================

       ██╗   ██╗████████╗██████╗ ██╗
       ╚██╗ ██╔╝╚══██╔══╝██╔══██╗██║
        ╚████╔╝    ██║   ██║  ██║██║
         ╚██╔╝     ██║   ██║  ██║██║
          ██║      ██║   ██████╔╝███████╗
          ╚═╝      ╚═╝   ╚═════╝ ╚══════╝ v1.5

       [*] YouTube Video Downloader
       [*] Created by: Rofi (Fixploit03)
       [*] Github: https://github.com/fixploit03/ytdl

============================================================
"""

def check_network_connection() -> bool:
    """Checks if there is an active internet connection."""
    try:
        socket.create_connection(("8.8.8.8", 53), timeout=5)
        return True
    except (socket.gaierror, socket.timeout, OSError):
        print("[-] No internet connection detected. Exiting...")
        sys.exit(1)

def clear_screen() -> None:
    """Clears the terminal screen based on the operating system."""
    try:
        if platform.system() == "Windows":
            os.system("cls")
        else:  # Linux, macOS, or other Unix-like systems
            os.system("clear")
    except OSError as e:
        print(f"[-] Failed to clear screen: {e}")
    except KeyboardInterrupt:
        print("\n[-] Program interrupted by user")
        sys.exit(0)

def show_banner() -> None:
    """Displays the program's ASCII art banner."""
    try:
        print(banner)
    except UnicodeEncodeError:
        print("[*] Displaying basic banner due to encoding issues:")
        print("YouTube Video Downloader v1.5 by Rofi (Fixploit03)")
    except Exception as e:
        print(f"[-] Failed to display banner: {e}")
    except KeyboardInterrupt:
        print("\n[-] Program interrupted by user")
        sys.exit(0)

def get_valid_input(prompt: str, validator_func=None, max_attempts: int = 3) -> str:
    """Gets validated user input with a retry limit."""
    attempts = 0
    while attempts < max_attempts:
        try:
            value = input(prompt).strip()
            if not value:
                print("[-] Input cannot be empty")
                attempts += 1
                continue
            value = value.strip('"').strip("'")
            if validator_func and not validator_func(value):
                print("[-] Invalid input")
                attempts += 1
                continue
            return value
        except UnicodeDecodeError:
            print("[-] Invalid character encoding detected")
            attempts += 1
        except EOFError:
            print("[-] Unexpected end of input detected")
            attempts += 1
        except Exception as e:
            print(f"[-] Error processing input: {e}")
            attempts += 1
    print(f"[-] Maximum attempts ({max_attempts}) reached, exiting...")
    sys.exit(1)

def is_valid_url(url: str) -> bool:
    """Validates if the URL is a valid YouTube URL."""
    try:
        if not isinstance(url, str):
            raise TypeError("URL must be a string")
        if not (url.startswith(("http://", "https://")) and "." in url):
            return False
        youtube_domains = ["youtube.com", "youtu.be"]
        if not any(domain in url.lower() for domain in youtube_domains):
            print("[-] Error: URL must be a valid YouTube URL (e.g., youtube.com or youtu.be)")
            return False
        return True
    except TypeError as e:
        print(f"[-] URL validation failed: {e}")
        return False
    except Exception as e:
        print(f"[-] Unexpected error in URL validation: {e}")
        return False
    except KeyboardInterrupt:
        print("\n[-] Program interrupted by user")
        sys.exit(0)

def is_valid_location(location: str) -> bool:
    """Validates if the save location is writable, handling OS-specific paths."""
    try:
        if not isinstance(location, str):
            raise TypeError("Location must be a string")
        location = os.path.normpath(os.path.abspath(location))
        dir_path = os.path.dirname(location) or location
        if not os.path.exists(dir_path):
            os.makedirs(dir_path, exist_ok=True)
            print(f"[*] Created directory: {dir_path}")
        if not os.access(dir_path, os.W_OK):
            print(f"[-] No write permission for: {dir_path}")
            return False
        return True
    except TypeError as e:
        print(f"[-] Invalid save location: {e}")
        return False
    except OSError as e:
        print(f"[-] Invalid save location: {e}")
        return False
    except Exception as e:
        print(f"[-] Error validating save location: {e}")
        return False
    except KeyboardInterrupt:
        print("\n[-] Program interrupted by user")
        sys.exit(0)

def check_ffmpeg() -> bool:
    """Checks if FFmpeg is installed and provides OS-specific installation instructions."""
    try:
        ffmpeg_path = shutil.which("ffmpeg")
        if ffmpeg_path is None:
            raise EnvironmentError("FFmpeg not found in system PATH")
        return True  # No output if FFmpeg is found
    except EnvironmentError:
        if platform.system() == "Windows":
            print("[-] FFmpeg not found in your system PATH.")
            print("[!] To install FFmpeg on Windows:")
            print("    1. Download FFmpeg from https://ffmpeg.org/download.html")
            print("    2. Extract the ZIP file to a folder (e.g., C:\\ffmpeg)")
            print("    3. Add the 'bin' folder to your PATH (e.g., C:\\ffmpeg\\bin)")
            print("    4. Restart your terminal and try again")
        else:  # Assuming Linux or Unix-like system
            print("[-] FFmpeg not found in your system PATH.")
            print("[!] To install FFmpeg on Linux:")
            print("    - On Ubuntu/Debian: Run 'sudo apt update && sudo apt install ffmpeg'")
            print("    - On Fedora: Run 'sudo dnf install ffmpeg'")
            print("    - On Arch: Run 'sudo pacman -S ffmpeg'")
            print("    - After installation, verify with 'ffmpeg -version'")
        print("[!] Exiting due to missing FFmpeg.")
        sys.exit(1)
    except Exception as e:
        print(f"[-] Error checking FFmpeg: {e}")
        return False
    except KeyboardInterrupt:
        print("\n[-] Program interrupted by user")
        sys.exit(0)

def get_video_formats(yt_url: str) -> Optional[List[List[str]]]:
    """Retrieves available MP4 video formats with the best quality per resolution."""
    check_network_connection()
    print("[*] Fetching available video formats...")
    try:
        ydl_opts = {'quiet': True, 'no_warnings': True, 'socket_timeout': 10}
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(yt_url, download=False)
            if info.get('availability') == 'unavailable':
                raise ValueError("Video is unavailable in your region or has been removed")
            formats = info.get('formats', [])
        if not formats:
            raise ValueError("No formats available for this video")

        video_dict = {}
        best_audio = None
        for f in formats:
            try:
                resolution = f'{f.get("height", "N/A")}p' if f.get('height') else 'N/A'
                filesize = f.get('filesize', 0) or 0
                format_id = f.get('format_id', 'N/A')
                if f.get('ext') == 'mp4' and f.get('vcodec') != 'none':
                    if (resolution not in video_dict or 
                        filesize > video_dict[resolution]['filesize']):
                        video_dict[resolution] = {
                            'format_id': format_id,
                            'resolution': resolution,
                            'filesize': filesize,
                            'has_audio': f.get('acodec') != 'none'
                        }
                elif f.get('ext') == 'mp4' and f.get('acodec') != 'none' and f.get('vcodec') == 'none':
                    if not best_audio or filesize > best_audio['filesize']:
                        best_audio = {'format_id': format_id, 'filesize': filesize}
            except (TypeError, ValueError) as e:
                print(f"[*] Skipping invalid format: {e}")
                continue

        table_data = []
        audio_id = best_audio['format_id'] if best_audio else 'bestaudio[ext=mp4]'
        for data in video_dict.values():
            if data['resolution'] != 'N/A':
                format_id = data['format_id'] if data['has_audio'] else f"{data['format_id']}+{audio_id}"
                table_data.append([
                    format_id,
                    data['resolution'],
                    f"{round(data['filesize'] / (1024 * 1024), 2)} MB" if data['filesize'] else 'N/A'
                ])
        table_data.sort(key=lambda x: int(x[1][:-1]) if x[1] != 'N/A' else 0, reverse=True)
        return table_data if table_data else None
    except yt_dlp.utils.DownloadError as e:
        print(f"[-] Failed to fetch formats: {e}")
        return None
    except ValueError as e:
        print(f"[-] {e}")
        return None
    except Exception as e:
        print(f"[-] Error fetching formats: {e}")
        return None
    except KeyboardInterrupt:
        print("\n[-] Program interrupted by user")
        sys.exit(0)

def download_video(yt_url: str, save_location: str, format_id: str = 'best', max_retries: int = 3) -> bool:
    """Downloads a single video with the specified format."""
    check_network_connection()
    attempt = 0
    try:
        save_location = os.path.normpath(os.path.abspath(save_location))
        ydl_opts = {
            'format': 'bestvideo[ext=mp4]+bestaudio[ext=mp4]/best[ext=mp4]' if format_id == 'best' else format_id,
            'outtmpl': os.path.join(save_location, '%(title)s.%(ext)s'),
            'merge_output_format': 'mp4',
            'socket_timeout': 30,
            'retries': 3,
            'fragment_retries': 3,
        }

        output_template = ydl_opts['outtmpl']
        existing_files = [f for f in os.listdir(save_location) if f.startswith(os.path.basename(output_template).split('.')[0])]
        if existing_files:
            choice = get_valid_input("[?] File already exists. Overwrite? (y/n): ", 
                                    lambda x: x.lower() in ['y', 'n'])
            if choice.lower() == 'n':
                print("[*] Download skipped")
                return True
            ydl_opts['overwrites'] = True

        while attempt < max_retries:
            try:
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    ydl.download([yt_url])
                print("[+] Download completed")
                return True
            except yt_dlp.utils.DownloadError as e:
                attempt += 1
                print(f"[-] Download attempt {attempt}/{max_retries} failed: {e}")
                if attempt < max_retries:
                    print("[*] Retrying in 5 seconds...")
                    time.sleep(5)
                else:
                    print("[-] Maximum retries reached")
                    return False
    except OSError as e:
        print(f"[-] File system error: {e}")
        return False
    except Exception as e:
        print(f"[-] Download error: {e}")
        return False
    except KeyboardInterrupt:
        print("\n[-] Program interrupted by user")
        sys.exit(0)

def read_url_file(file_path: str) -> List[str]:
    """Reads a list of YouTube URLs from a text file."""
    urls = []
    try:
        file_path = os.path.normpath(file_path)
        if not os.path.isfile(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")
        with open(file_path, 'r', encoding='utf-8') as f:
            for i, line in enumerate(f, 1):
                url = line.strip()
                if not url:
                    continue
                if is_valid_url(url):
                    urls.append(url)
                else:
                    print(f"[-] Skipping invalid URL at line {i}: {url}")
        if not urls:
            raise ValueError("No valid YouTube URLs found in the file")
        print(f"[*] Loaded {len(urls)} valid URLs from {file_path}")
        return urls
    except FileNotFoundError as e:
        print(f"[-] {e}")
        return []
    except UnicodeDecodeError:
        print(f"[-] File {file_path} contains invalid encoding")
        return []
    except PermissionError as e:
        print(f"[-] Permission denied: {e}")
        return []
    except Exception as e:
        print(f"[-] Error reading file: {e}")
        return []
    except KeyboardInterrupt:
        print("\n[-] Program interrupted by user")
        sys.exit(0)

def check_playlist(playlist_url: str) -> int:
    """Checks the number of videos in a YouTube playlist."""
    check_network_connection()
    try:
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'socket_timeout': 10,
            'simulate': True,
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(playlist_url, download=False)
            if 'entries' in info:
                video_count = len(info['entries'])
                if video_count == 0:
                    raise ValueError("No videos found in the playlist")
                return video_count
            elif 'playlist_count' in info and info['playlist_count'] > 0:
                return info['playlist_count']
            else:
                raise ValueError("URL is not a valid playlist or contains no videos")
    except yt_dlp.utils.DownloadError as e:
        print(f"[-] Failed to check playlist: {e}")
        return 0
    except ValueError as e:
        print(f"[-] {e}")
        return 0
    except Exception as e:
        print(f"[-] Error checking playlist: {e}")
        return 0
    except KeyboardInterrupt:
        print("\n[-] Program interrupted by user")
        sys.exit(0)

def download_playlist(playlist_url: str, save_location: str, max_retries: int = 3) -> bool:
    """Downloads all videos in a YouTube playlist."""
    check_network_connection()
    attempt = 0
    try:
        save_location = os.path.normpath(os.path.abspath(save_location))
        ydl_opts = {
            'format': 'bestvideo[ext=mp4]+bestaudio[ext=mp4]/best[ext=mp4]',
            'outtmpl': os.path.join(save_location, '%(playlist_title)s', '%(title)s.%(ext)s'),
            'merge_output_format': 'mp4',
            'socket_timeout': 30,
            'retries': 3,
            'fragment_retries': 3,
            'noplaylist': False,
            'overwrites': True,
        }

        while attempt < max_retries:
            try:
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    ydl.download([playlist_url])
                print("[+] Playlist download completed")
                return True
            except yt_dlp.utils.DownloadError as e:
                attempt += 1
                print(f"[-] Playlist download attempt {attempt}/{max_retries} failed: covered{e}")
                if attempt < max_retries:
                    print("[*] Retrying in 5 seconds...")
                    time.sleep(5)
                else:
                    print("[-] Maximum retries reached")
                    return False
    except OSError as e:
        print(f"[-] File system error: {e}")
        return False
    except Exception as e:
        print(f"[-] Error downloading playlist: {e}")
        return False
    except KeyboardInterrupt:
        print("\n[-] Program interrupted by user")
        sys.exit(0)

def show_support_message() -> None:
    """Displays a support message for the developer."""
    try:
        clear_screen()
        show_banner()
        print("""       [*] Support the Developer:
       --------------------------
       Thank you for using this program! If you find it helpful, please consider supporting me:
        
       - GitHub: https://github.com/fixploit03
       - Donation: https://saweria.co/fixploit03
        
       Your support is greatly appreciated!
        """)
        input("[*] Press Enter to return to the menu...")
    except Exception as e:
        print(f"[-] Error displaying support message: {e}")
    except KeyboardInterrupt:
        print("\n[-] Program interrupted by user")
        sys.exit(0)

def main() -> None:
    """Main function with menu for single URL, URL list, playlist download, support, or exit."""
    while True:
        try:
            check_network_connection()

            clear_screen()
            show_banner()

            if not check_ffmpeg():
                sys.exit(1)  # Exit after OS-specific FFmpeg error message

            print("       [*] Select download mode:")
            print("       -------------------------")
            print("       0. Support Developer")
            print("       1. Single URL")
            print("       2. List of URLs from file")
            print("       3. Playlist")
            print("       4. Exit\n")
            mode = get_valid_input("[#] Enter your choice (0-4): ", 
                                  lambda x: x in ['0', '1', '2', '3', '4'])

            if mode == '0':
                show_support_message()
                continue

            elif mode == '1':
                try:
                    yt_url = get_valid_input("[#] Enter YouTube URL: ", is_valid_url)
                    save_location = get_valid_input("[#] Enter save location: ", is_valid_location)
                    choice = get_valid_input("[?] Use best resolution? (y/n): ", 
                                           lambda x: x.lower() in ['y', 'n']).lower()
                    if choice == 'y':
                        print(f"[*] Downloading video: {yt_url}", end="")
                        success = download_video(yt_url, save_location)
                    else:
                        formats = get_video_formats(yt_url)
                        if not formats:
                            print("[-] No suitable MP4 formats available")
                            continue
                        print("[+] Available video formats:")
                        print(tabulate(formats, headers=["ID", "Resolution", "File Size"], tablefmt="pretty"))
                        valid_ids = [row[0] for row in formats]
                        format_id = get_valid_input("[#] Enter format ID: ", 
                                                  lambda x: x in valid_ids)
                        print(f"[*] Downloading video: {yt_url}", end="")
                        success = download_video(yt_url, save_location, format_id)
                    if not success:
                        raise RuntimeError("Download failed")
                except RuntimeError as e:
                    print(f"[-] {e}")

            elif mode == '2':
                try:
                    file_path = get_valid_input("[#] Enter path to URL file: ", 
                                               lambda x: os.path.isfile(os.path.normpath(x)))
                    print("[*] Checking URL file...")
                    urls = read_url_file(file_path)
                    if not urls:
                        raise ValueError("No valid URLs found to process")
                    print(f"[+] Found {len(urls)} valid YouTube URLs")
                    save_location = get_valid_input("[#] Enter save location: ", is_valid_location)
                    success = True
                    for i, url in enumerate(urls, 1):
                        print(f"[*] Downloading video {i}/{len(urls)}: {url}", end="")
                        if not download_video(url, save_location):
                            success = False
                            print(f"[-] Failed to download: {url}")
                    if not success:
                        raise RuntimeError("One or more downloads failed")
                except ValueError as e:
                    print(f"[-] {e}")
                except RuntimeError as e:
                    print(f"[-] {e}")

            elif mode == '3':
                try:
                    playlist_url = get_valid_input("[#] Enter playlist URL: ", is_valid_url)
                    print("[*] Checking playlist contents...")
                    video_count = check_playlist(playlist_url)
                    if video_count == 0:
                        continue
                    print(f"[+] Found {video_count} videos in the playlist")
                    save_location = get_valid_input("[#] Enter save location: ", is_valid_location)
                    print(f"[*] Downloading playlist: {playlist_url}", end="")
                    success = download_playlist(playlist_url, save_location)
                    if not success:
                        raise RuntimeError("Playlist download failed")
                except RuntimeError as e:
                    print(f"[-] {e}")

            elif mode == '4':
                print("[*] Thank you for using YTDL!")
                sys.exit(0)

            print("[*] Operation completed successfully")
            input("[*] Press Enter to return to the menu...")

        except KeyboardInterrupt:
            print("\n[-] Program interrupted by user")
            sys.exit(0)
        except Exception as e:
            print(f"[-] Critical error: {e}")
            input("[*] Press Enter to return to the menu...")

if __name__ == "__main__":
    main()
