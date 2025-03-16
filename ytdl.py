import yt_dlp
import os
import sys
import platform
from tabulate import tabulate
from typing import List, Optional
import logging

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
          ╚═╝      ╚═╝   ╚═════╝ ╚══════╝ v1.2
          
       [*] YouTube Video Downloader          
       [*] Created by: Rofi (Fixploit03)     
       [*] Github: https://github.com/fixploit03/ytdl       
       
============================================================
"""

def clear_screen() -> None:
    """Clear the terminal screen based on OS."""
    try:
        os.system("cls" if platform.system() == "Windows" else "clear")
    except Exception as e:
        logging.error(f"Failed to clear screen: {str(e)}")
        print("[-] Screen clearing failed, continuing execution...")

def show_banner() -> None:
    """Display program banner."""
    try:
        print(banner)
    except UnicodeEncodeError:
        print("[*] Basic banner display due to encoding issues:")
        print("YouTube Video Downloader v1.2 by Rofi (Fixploit03)")
    except Exception as e:
        logging.error(f"Banner display failed: {str(e)}")
        print("[-] Banner display failed")

def get_valid_input(prompt: str, validator_func=None) -> str:
    """Get validated user input with error handling."""
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
    """Validate if the URL is a valid YouTube URL."""
    try:
        # Check if it starts with http:// or https:// and contains a dot
        if not (url.startswith(("http://", "https://")) and "." in url):
            return False
        # Check if it's a YouTube URL
        youtube_domains = ["youtube.com", "youtu.be"]
        if not any(domain in url.lower() for domain in youtube_domains):
            print("[-] Error: URL must be a YouTube URL (e.g., youtube.com or youtu.be)")
            return False
        return True
    except AttributeError:
        return False

def is_valid_location(location: str) -> bool:
    """Validate save location."""
    try:
        location = os.path.abspath(location)
        if not os.path.exists(os.path.dirname(location) or location):
            print(f"[-] Directory doesn't exist: {location}")
            return False
        if not os.access(os.path.dirname(location) or location, os.W_OK):
            print(f"[-] No write permission: {location}")
            return False
        return True
    except OSError as e:
        logging.error(f"Location validation error: {str(e)}")
        print(f"[-] Invalid path: {str(e)}")
        return False

def check_ffmpeg() -> bool:
    """Check FFmpeg installation."""
    try:
        cmd = "ffmpeg -version >nul 2>&1" if platform.system() == "Windows" else "ffmpeg -version >/dev/null 2>&1"
        result = os.system(cmd)
        if result != 0:
            raise EnvironmentError("FFmpeg not found")
        return True
    except Exception as e:
        logging.error(f"FFmpeg check failed: {str(e)}")
        print(f"[-] FFmpeg check failed: {str(e)}")
        return False

def get_video_formats(yt_url: str) -> Optional[List[List[str]]]:
    """Get all available video formats (mp4) with best quality per resolution, including audio."""
    print("[*] Fetching video resolutions...")  # Indicate that resolution fetching is in progress
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

        # Dictionary to store the best video formats by resolution
        video_dict = {}
        # Find the best audio in mp4
        best_audio = None
        
        for f in formats:
            try:
                resolution = f'{f.get("height", "N/A")}p' if f.get('height') else 'N/A'
                filesize = f.get('filesize', 0) or 0
                format_id = f.get('format_id', 'N/A')
                
                # Filter mp4 video formats (with or without audio)
                if f.get('ext') == 'mp4' and f.get('vcodec') != 'none':
                    if (resolution not in video_dict or 
                        filesize > video_dict[resolution]['filesize']):
                        video_dict[resolution] = {
                            'format_id': format_id,
                            'resolution': resolution,
                            'filesize': filesize,
                            'has_audio': f.get('acodec') != 'none'
                        }
                # Filter the best mp4 audio
                elif f.get('ext') == 'mp4' and f.get('acodec') != 'none' and f.get('vcodec') == 'none':
                    if not best_audio or filesize > best_audio['filesize']:
                        best_audio = {
                            'format_id': format_id,
                            'filesize': filesize,
                        }
            except (TypeError, ValueError) as e:
                logging.warning(f"Format parsing error: {str(e)}")
                continue

        # Combine video with the best audio if needed
        table_data = []
        audio_id = best_audio['format_id'] if best_audio else 'bestaudio[ext=mp4]'
        for data in video_dict.values():
            if data['resolution'] != 'N/A':
                # If the video already has audio, use it directly
                if data['has_audio']:
                    combined_format_id = data['format_id']
                else:
                    # Otherwise, combine with the best audio
                    combined_format_id = f"{data['format_id']}+{audio_id}"
                table_data.append([
                    combined_format_id,
                    data['resolution'],
                    f"{round(data['filesize'] / (1024 * 1024), 2)} MB" if data['filesize'] else 'N/A',
                ])
        
        # Sort by resolution (highest to lowest)
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
    """Download video with specified format."""
    try:
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
    """Main program execution."""
    try:
        clear_screen()
        show_banner()
        
        if not check_ffmpeg():
            print("[-] FFmpeg is required to continue")
            sys.exit(1)
            
        yt_url = get_valid_input("[#] Enter YouTube URL: ", is_valid_url)
        save_location = get_valid_input("[#] Enter save location: ", is_valid_location)
        
        choice = get_valid_input("[?] Best resolution (y/n): ", 
                               lambda x: x.lower() in ['y', 'n']).lower()
        
        if choice == 'y':
            success = download_video(yt_url, save_location)
        else:
            formats = get_video_formats(yt_url)
            if not formats:
                print("[-] No suitable mp4 formats found")
                sys.exit(1)
            print("[+] Video resolutions found:")  # Indicate that resolutions have been found
            print(tabulate(formats, headers=["ID", "Resolution", "File Size"], 
                         tablefmt="pretty"))
            valid_ids = [row[0] for row in formats]
            format_id = get_valid_input("[#] Enter video ID: ", 
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
