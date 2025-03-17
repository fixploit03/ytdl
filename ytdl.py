import yt_dlp
import os
import sys
import platform
from tabulate import tabulate
from typing import List, Optional
import logging
from logging.handlers import RotatingFileHandler
import shutil
import time

# Setup logging with rotation to prevent log file bloat
logger = logging.getLogger('ytdl')
logger.setLevel(logging.INFO)
handler = RotatingFileHandler('ytdl.log', maxBytes=1024*1024, backupCount=3)
handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
logger.addHandler(handler)

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

def clear_screen() -> None:
    """Clears the terminal screen based on the operating system.

    Uses 'cls' command on Windows and 'clear' on Unix-based systems.
    Handles potential errors and user interrupts gracefully.
    """
    try:
        os.system("cls" if platform.system() == "Windows" else "clear")
    except OSError as e:
        logger.error(f"Failed to clear screen: {e}")
        print("[-] Failed to clear screen, continuing execution...")
    except KeyboardInterrupt:
        logger.info("Program interrupted by user during screen clear")
        print("\n[-] Program interrupted by user")
        sys.exit(0)

def show_banner() -> None:
    """Displays the program's ASCII art banner.

    Attempts to print the banner, falling back to a simpler version if encoding fails.
    Handles unexpected errors and user interrupts.
    """
    try:
        print(banner)
    except UnicodeEncodeError:
        logger.warning("Unicode encoding issue in banner display")
        print("[*] Displaying basic banner due to encoding issues:")
        print("YouTube Video Downloader v1.5 by Rofi (Fixploit03)")
    except Exception as e:
        logger.error(f"Failed to display banner: {e}")
        print("[-] Failed to display banner")
    except KeyboardInterrupt:
        logger.info("Program interrupted by user during banner display")
        print("\n[-] Program interrupted by user")
        sys.exit(0)

def get_valid_input(prompt: str, validator_func=None, max_attempts: int = 3) -> str:
    """Gets validated user input with a retry limit.

    Args:
        prompt (str): Message to display for input.
        validator_func (callable, optional): Function to validate input. Defaults to None.
        max_attempts (int): Maximum attempts before giving up. Defaults to 3.

    Returns:
        str: Validated user input.

    Raises:
        SystemExit: If max attempts are exceeded or user interrupts the program.
    """
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
            logger.error("Invalid character encoding in input")
            print("[-] Invalid character encoding detected")
            attempts += 1
        except EOFError:
            logger.error("EOF detected during input")
            print("[-] Unexpected end of input detected")
            attempts += 1
        except Exception as e:
            logger.error(f"Unexpected input error: {e}")
            print(f"[-] Error processing input: {e}")
            attempts += 1
    logger.error(f"Maximum input attempts ({max_attempts}) exceeded")
    print(f"[-] Maximum attempts ({max_attempts}) reached, exiting...")
    sys.exit(1)

def is_valid_url(url: str) -> bool:
    """Validates if the URL is a valid YouTube URL.

    Args:
        url (str): The URL to validate.

    Returns:
        bool: True if the URL is a valid YouTube URL, False otherwise.
    """
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
        logger.error(f"URL validation failed: {e}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error in URL validation: {e}")
        return False
    except KeyboardInterrupt:
        logger.info("Program interrupted by user during URL validation")
        print("\n[-] Program interrupted by user")
        sys.exit(0)

def is_valid_location(location: str) -> bool:
    """Validates if the save location is writable.

    Args:
        location (str): The file path to validate.

    Returns:
        bool: True if the location is writable, False otherwise.
    """
    try:
        if not isinstance(location, str):
            raise TypeError("Location must be a string")
        location = os.path.abspath(location)
        dir_path = os.path.dirname(location) or location
        if not os.path.exists(dir_path):
            os.makedirs(dir_path, exist_ok=True)
            logger.info(f"Created directory: {dir_path}")
        if not os.access(dir_path, os.W_OK):
            print(f"[-] No write permission for: {dir_path}")
            return False
        return True
    except TypeError as e:
        logger.error(f"Location validation failed: {e}")
        print(f"[-] Invalid save location: {e}")
        return False
    except OSError as e:
        logger.error(f"Location validation failed: {e}")
        print(f"[-] Invalid save location: {e}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error in location validation: {e}")
        print(f"[-] Error validating save location: {e}")
        return False
    except KeyboardInterrupt:
        logger.info("Program interrupted by user during location validation")
        print("\n[-] Program interrupted by user")
        sys.exit(0)

def check_ffmpeg() -> bool:
    """Checks if FFmpeg is installed and available in the system PATH.

    Returns:
        bool: True if FFmpeg is found, False otherwise.
    """
    try:
        ffmpeg_path = shutil.which("ffmpeg")
        if ffmpeg_path is None:
            raise EnvironmentError("FFmpeg not found in system PATH")
        logger.info(f"FFmpeg found at: {ffmpeg_path}")
        return True
    except EnvironmentError as e:
        logger.error(f"FFmpeg check failed: {e}")
        print(f"[-] FFmpeg not found: {e}")
        print("[!] Please install FFmpeg: https://ffmpeg.org/download.html")
        return False
    except Exception as e:
        logger.error(f"Unexpected error checking FFmpeg: {e}")
        print(f"[-] Error checking FFmpeg: {e}")
        return False
    except KeyboardInterrupt:
        logger.info("Program interrupted by user during FFmpeg check")
        print("\n[-] Program interrupted by user")
        sys.exit(0)

def get_video_formats(yt_url: str) -> Optional[List[List[str]]]:
    """Retrieves available MP4 video formats with the best quality per resolution.

    Args:
        yt_url (str): The YouTube URL to fetch formats from.

    Returns:
        Optional[List[List[str]]]: A list of format details (ID, resolution, size) or None if unavailable.
    """
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
                logger.warning(f"Skipping invalid format: {e}")
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
        logger.error(f"Failed to fetch formats: {e}")
        print(f"[-] Failed to fetch formats: {e}")
        return None
    except ValueError as e:
        logger.error(f"Video unavailable: {e}")
        print(f"[-] {e}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error fetching formats: {e}")
        print(f"[-] Error fetching formats: {e}")
        return None
    except KeyboardInterrupt:
        logger.info("Program interrupted by user during format fetching")
        print("\n[-] Program interrupted by user")
        sys.exit(0)

def download_video(yt_url: str, save_location: str, format_id: str = 'best', max_retries: int = 3) -> bool:
    """Downloads a single video with the specified format.

    Args:
        yt_url (str): The YouTube URL to download.
        save_location (str): The directory to save the video.
        format_id (str): The format ID to download (default is 'best'). Defaults to 'best'.
        max_retries (int): Maximum retry attempts for failed downloads. Defaults to 3.

    Returns:
        bool: True if download succeeds, False otherwise.
    """
    attempt = 0
    try:
        save_location = os.path.abspath(save_location)
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
                logger.info(f"Download completed for {yt_url}")
                print("[+] Download completed")
                return True
            except yt_dlp.utils.DownloadError as e:
                attempt += 1
                logger.error(f"Download attempt {attempt}/{max_retries} failed: {e}")
                print(f"[-] Download failed: {e}")
                if attempt < max_retries:
                    print("[*] Retrying in 5 seconds...")
                    time.sleep(5)
                else:
                    print("[-] Maximum retries reached")
                    return False
    except OSError as e:
        logger.error(f"File system error during download: {e}")
        print(f"[-] File system error: {e}")
        return False
    except Exception as e:
        logger.error(f"Unexpected download error: {e}")
        print(f"[-] Download error: {e}")
        return False
    except KeyboardInterrupt:
        logger.info("Program interrupted by user during video download")
        print("\n[-] Program interrupted by user")
        sys.exit(0)

def read_url_file(file_path: str) -> List[str]:
    """Reads a list of YouTube URLs from a text file.

    Args:
        file_path (str): The path to the text file containing URLs.

    Returns:
        List[str]: A list of valid YouTube URLs found in the file.
    """
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
                    logger.warning(f"Invalid URL at line {i}: {url}")
                    print(f"[-] Skipping invalid URL at line {i}: {url}")
        if not urls:
            raise ValueError("No valid YouTube URLs found in the file")
        logger.info(f"Loaded {len(urls)} valid URLs from {file_path}")
        return urls
    except FileNotFoundError as e:
        logger.error(f"{e}")
        print(f"[-] {e}")
        return []
    except UnicodeDecodeError:
        logger.error(f"File {file_path} contains invalid encoding")
        print(f"[-] File contains invalid encoding")
        return []
    except PermissionError as e:
        logger.error(f"Permission denied for file {file_path}: {e}")
        print(f"[-] Permission denied: {e}")
        return []
    except Exception as e:
        logger.error(f"Error reading URL file: {e}")
        print(f"[-] Error reading file: {e}")
        return []
    except KeyboardInterrupt:
        logger.info("Program interrupted by user during file reading")
        print("\n[-] Program interrupted by user")
        sys.exit(0)

def check_playlist(playlist_url: str) -> int:
    """Checks the number of videos in a YouTube playlist.

    Args:
        playlist_url (str): The YouTube playlist URL to check.

    Returns:
        int: The number of videos in the playlist, or 0 if an error occurs.
    """
    try:
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'socket_timeout': 10,
            'simulate': True,  # Hanya simulasi, tidak download
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(playlist_url, download=False)
            # Jika URL adalah playlist
            if 'entries' in info:
                video_count = len(info['entries'])
                if video_count == 0:
                    raise ValueError("No videos found in the playlist")
                return video_count
            # Jika URL adalah video tunggal dengan parameter list
            elif 'playlist_count' in info and info['playlist_count'] > 0:
                return info['playlist_count']
            else:
                raise ValueError("URL is not a valid playlist or contains no videos")
    except yt_dlp.utils.DownloadError as e:
        logger.error(f"Failed to check playlist: {e}")
        print(f"[-] Failed to check playlist: {e}")
        return 0
    except ValueError as e:
        logger.error(f"Playlist error: {e}")
        print(f"[-] {e}")
        return 0
    except Exception as e:
        logger.error(f"Unexpected error checking playlist: {e}")
        print(f"[-] Error checking playlist: {e}")
        return 0
    except KeyboardInterrupt:
        logger.info("Program interrupted by user during playlist check")
        print("\n[-] Program interrupted by user")
        sys.exit(0)

def download_playlist(playlist_url: str, save_location: str, max_retries: int = 3) -> bool:
    """Downloads all videos in a YouTube playlist.

    Args:
        playlist_url (str): The YouTube playlist URL to download.
        save_location (str): The directory to save the videos.
        max_retries (int): Maximum retry attempts for failed downloads. Defaults to 3.

    Returns:
        bool: True if download succeeds, False otherwise.
    """
    attempt = 0
    try:
        save_location = os.path.abspath(save_location)
        ydl_opts = {
            'format': 'bestvideo[ext=mp4]+bestaudio[ext=mp4]/best[ext=mp4]',
            'outtmpl': os.path.join(save_location, '%(playlist_title)s/%(title)s.%(ext)s'),
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
                logger.info(f"Playlist download completed for {playlist_url}")
                print("[+] Playlist download completed")
                return True
            except yt_dlp.utils.DownloadError as e:
                attempt += 1
                logger.error(f"Playlist download attempt {attempt}/{max_retries} failed: {e}")
                print(f"[-] Playlist download failed: {e}")
                if attempt < max_retries:
                    print("[*] Retrying in 5 seconds...")
                    time.sleep(5)
                else:
                    print("[-] Maximum retries reached")
                    return False
    except OSError as e:
        logger.error(f"File system error during playlist download: {e}")
        print(f"[-] File system error: {e}")
        return False
    except Exception as e:
        logger.error(f"Unexpected playlist download error: {e}")
        print(f"[-] Error downloading playlist: {e}")
        return False
    except KeyboardInterrupt:
        logger.info("Program interrupted by user during playlist download")
        print("\n[-] Program interrupted by user")
        sys.exit(0)

def show_support_message() -> None:
    """Displays a support message for the developer.

    Clears the screen, shows the banner, and provides support information.
    """
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
        logger.error(f"Error displaying support message: {e}")
        print(f"[-] Error displaying support message: {e}")
    except KeyboardInterrupt:
        logger.info("Program interrupted by user during support message display")
        print("\n[-] Program interrupted by user")
        sys.exit(0)

def main() -> None:
    """Main function with menu for single URL, URL list, playlist download, support, or exit.

    Runs an infinite loop displaying a menu and handling user choices until exit is selected.
    """
    while True:
        try:
            clear_screen()
            show_banner()

            if not check_ffmpeg():
                print("[-] FFmpeg is required to run this program")
                sys.exit(1)

            # Display menu
            print("       [*] Select download mode:")
            print("       -------------------------")
            print("       0. Support Developer")
            print("       1. Single URL")
            print("       2. List of URLs from file")
            print("       3. Playlist")
            print("       4. Exit\n")
            mode = get_valid_input("[#] Enter your choice (0-4): ", 
                                  lambda x: x in ['0', '1', '2', '3', '4'])

            if mode == '0':  # Support Developer
                show_support_message()
                continue

            elif mode == '1':  # Single URL
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
                    logger.error(f"Single URL download failed: {e}")
                    print(f"[-] {e}")

            elif mode == '2':  # List of URLs from file
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
                            logger.warning(f"Failed to download {url}")
                            print(f"[-] Failed to download: {url}")
                    if not success:
                        raise RuntimeError("One or more downloads failed")
                except ValueError as e:
                    logger.error(f"URL list download failed: {e}")
                    print(f"[-] {e}")
                except RuntimeError as e:
                    logger.error(f"URL list download completed with errors: {e}")
                    print(f"[-] {e}")

            elif mode == '3':  # Playlist
                try:
                    playlist_url = get_valid_input("[#] Enter playlist URL: ", is_valid_url)
                    print("[*] Checking playlist contents...")
                    video_count = check_playlist(playlist_url)
                    if video_count == 0:
                        continue  # Kembali ke menu jika playlist tidak valid
                    print(f"[+] Found {video_count} videos in the playlist")
                    save_location = get_valid_input("[#] Enter save location: ", is_valid_location)
                    print(f"[*] Downloading playlist: {playlist_url}", end="")
                    success = download_playlist(playlist_url, save_location)
                    if not success:
                        raise RuntimeError("Playlist download failed")
                except RuntimeError as e:
                    logger.error(f"Playlist download failed: {e}")
                    print(f"[-] {e}")

            elif mode == '4':  # Exit
                print("[*] Thank you for using YTDL!")
                sys.exit(0)

            # Jika sukses, tampilkan pesan selesai
            print("[*] Operation completed successfully")
            input("[*] Press Enter to return to the menu...")

        except KeyboardInterrupt:
            logger.info("Program interrupted by user at menu")
            print("\n[-] Program interrupted by user")
            sys.exit(0)
        except Exception as e:
            logger.critical(f"Critical error in program execution: {e}")
            print(f"[-] Critical error: {e}")
            input("[*] Press Enter to return to the menu...")

if __name__ == "__main__":
    main()
