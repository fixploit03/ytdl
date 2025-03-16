import yt_dlp
import os
import sys
import platform
from tabulate import tabulate
from typing import List, Optional
import logging
import shutil

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    filename='ytdl.log'
)

# Banner
banner = """
============================================================

       ██╗   ██╗████████╗██████╗ ██╗
       ╚██╗ ██╔╝╚══██╔══╝██╔══██╗██║
        ╚████╔╝    ██║   ██║  ██║██║
         ╚██╔╝     ██║   ██║  ██║██║
          ██║      ██║   ██████╔╝███████╗
          ╚═╝      ╚═╝   ╚═════╝ ╚══════╝ v1.3
          
       [*] YouTube Video Downloader          
       [*] Created by: Rofi (Fixploit03)     
       [*] Github: https://github.com/fixploit03/ytdl       
       
============================================================
"""

def clear_screen() -> None:
    """
    Clears the terminal screen based on the operating system.

    Notes:
        - Uses 'cls' for Windows and 'clear' for Linux/Unix.
        - Handles errors if screen clearing fails.
    """
    try:
        os.system("cls" if platform.system() == "Windows" else "clear")
    except Exception as e:
        logging.error(f"Failed to clear screen: {str(e)}")
        print("[-] Screen clearing failed, continuing execution...")

def show_banner() -> None:
    """
    Displays the program's ASCII art banner.

    Notes:
        - Handles Unicode encoding issues with a simple fallback.
        - Logs errors if banner display fails.
    """
    try:
        print(banner)
    except UnicodeEncodeError:
        print("[*] Basic banner display due to encoding issues:")
        print("YouTube Video Downloader v1.3 by Rofi (Fixploit03)")
    except Exception as e:
        logging.error(f"Banner display failed: {str(e)}")
        print("[-] Banner display failed")

def get_valid_input(prompt: str, validator_func=None) -> str:
    """
    Gets validated user input with optional validation.

    Args:
        prompt (str): Message displayed to request input.
        validator_func (callable, optional): Function to validate input.

    Returns:
        str: Validated user input.

    Raises:
        SystemExit: If the user terminates the program with Ctrl+C.
    """
    while True:
        try:
            value = input(prompt).strip()
            if not value:
                print("[-] Input cannot be empty")
                continue
            if validator_func and not validator_func(value):
                print("[-] Invalid input format")
                continue
            return value
        except UnicodeDecodeError:
            print("[-] Invalid character encoding detected")
            continue
        except KeyboardInterrupt:
            logging.info("Program terminated by user")
            print("\n[-] Program terminated by user")
            sys.exit(1)
        except Exception as e:
            logging.error(f"Input error: {str(e)}")
            print(f"[-] Input error occurred: {str(e)}")

def is_valid_url(url: str) -> bool:
    """
    Validates if the URL is a valid YouTube URL.

    Args:
        url (str): URL to validate.

    Returns:
        bool: True if the URL is valid, False otherwise.
    """
    try:
        if not (url.startswith(("http://", "https://")) and "." in url):
            return False
        youtube_domains = ["youtube.com", "youtu.be"]
        if not any(domain in url.lower() for domain in youtube_domains):
            print("[-] Error: URL must be a YouTube URL (e.g., youtube.com or youtu.be)")
            return False
        return True
    except AttributeError:
        return False

def is_valid_location(location: str) -> bool:
    """
    Validates the save location for both Windows and Linux.

    Args:
        location (str): File save location path.

    Returns:
        bool: True if the location is valid and writable, False otherwise.
    """
    try:
        location = os.path.abspath(location)
        dir_path = os.path.dirname(location) or location
        
        if not os.path.exists(dir_path):
            try:
                os.makedirs(dir_path, exist_ok=True)
                logging.info(f"Created directory: {dir_path}")
            except OSError as e:
                print(f"[-] Cannot create directory {dir_path}: {str(e)}")
                return False
        
        if not os.access(dir_path, os.W_OK):
            print(f"[-] No write permission: {dir_path}")
            return False
        return True
    except OSError as e:
        logging.error(f"Location validation error: {str(e)}")
        print(f"[-] Invalid path: {str(e)}")
        return False

def check_ffmpeg() -> bool:
    """
    Checks if FFmpeg is installed and available in the system PATH.

    Returns:
        bool: True if FFmpeg is found, False otherwise.

    Notes:
        - Uses shutil.which for more robust detection.
    """
    try:
        ffmpeg_path = shutil.which("ffmpeg")
        if ffmpeg_path is None:
            raise EnvironmentError("FFmpeg not found in PATH")
        logging.info(f"FFmpeg found at: {ffmpeg_path}")
        return True
    except Exception as e:
        logging.error(f"FFmpeg check failed: {str(e)}")
        print(f"[-] FFmpeg check failed: {str(e)}")
        print("[-] Please install FFmpeg and ensure it's in your system PATH")
        return False

def get_video_formats(yt_url: str) -> Optional[List[List[str]]]:
    """
    Retrieves all available MP4 video formats with the best quality per resolution.

    Args:
        yt_url (str): YouTube URL to analyze.

    Returns:
        Optional[List[List[str]]]: List of formats (ID, resolution, file size) or None if failed.
    """
    print("[*] Fetching video resolutions...")
    try:
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'socket_timeout': 10,
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(yt_url, download=False)
            formats = info.get('formats', [])
            
        if not formats:
            raise ValueError("No formats available")

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
                        best_audio = {
                            'format_id': format_id,
                            'filesize': filesize,
                        }
            except (TypeError, ValueError) as e:
                logging.warning(f"Format parsing error: {str(e)}")
                continue

        table_data = []
        audio_id = best_audio['format_id'] if best_audio else 'bestaudio[ext=mp4]'
        for data in video_dict.values():
            if data['resolution'] != 'N/A':
                if data['has_audio']:
                    combined_format_id = data['format_id']
                else:
                    combined_format_id = f"{data['format_id']}+{audio_id}"
                table_data.append([
                    combined_format_id,
                    data['resolution'],
                    f"{round(data['filesize'] / (1024 * 1024), 2)} MB" if data['filesize'] else 'N/A',
                ])
        
        table_data.sort(key=lambda x: int(x[1][:-1]), reverse=True)
        return table_data if table_data else None

    except yt_dlp.utils.DownloadError as e:
        logging.error(f"Download error getting formats: {str(e)}")
        print(f"[-] Failed to get formats: {str(e)}")
        return None
    except Exception as e:
        logging.error(f"Unexpected error getting formats: {str(e)}")
        print(f"[-] Error fetching formats: {str(e)}")
        return None

def download_video(yt_url: str, save_location: str, format_id: str = 'best') -> bool:
    """
    Downloads a video with the specified format.

    Args:
        yt_url (str): YouTube URL to download.
        save_location (str): File save location.
        format_id (str): Video format ID, default is 'best'.

    Returns:
        bool: True if download succeeds, False otherwise.
    """
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
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([yt_url])
        logging.info(f"Download completed for {yt_url}")
        print("[+] Download completed")
        return True
    except yt_dlp.utils.DownloadError as e:
        logging.error(f"Download failed: {str(e)}")
        print(f"[-] Download failed: {str(e)}")
        return False
    except Exception as e:
        logging.error(f"Download error: {str(e)}")
        print(f"[-] Download error: {str(e)}")
        return False

def main() -> None:
    """
    Main execution of the YouTube Video Downloader program.

    Notes:
        - Checks for FFmpeg, prompts for URL and location, then downloads the video.
        - Offers a choice between best resolution or manual selection.
    """
    try:
        clear_screen()
        show_banner()
        
        if not check_ffmpeg():
            print("[-] FFmpeg is required to continue")
            sys.exit(1)
            
        yt_url = get_valid_input("[#] Enter YouTube URL: ", is_valid_url)
        save_location = get_valid_input("[#] Enter save location: ", is_valid_location)
        
        choice = get_valid_input("[?] Use best resolution (y/n): ", 
                               lambda x: x.lower() in ['y', 'n']).lower()
        
        if choice == 'y':
            success = download_video(yt_url, save_location)
        else:
            formats = get_video_formats(yt_url)
            if not formats:
                print("[-] No suitable MP4 formats found")
                sys.exit(1)
            print("[+] Available video resolutions:")
            print(tabulate(formats, headers=["ID", "Resolution", "File Size"], 
                         tablefmt="pretty"))
            valid_ids = [row[0] for row in formats]
            format_id = get_valid_input("[#] Enter video format ID: ", 
                                      lambda x: x in valid_ids)
            success = download_video(yt_url, save_location, format_id)
            
        if not success:
            sys.exit(1)
            
    except Exception as e:
        logging.critical(f"Main execution failed: {str(e)}")
        print(f"[-] Critical error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
