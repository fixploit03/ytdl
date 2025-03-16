import yt_dlp
import os
import sys
import platform

#---------------------------------------------------------------------
# Program python sederhana untuk mendownload video dari Youtube
# Dibuat oleh: Rofi (Fixploit03)
#---------------------------------------------------------------------
#
# Library yang digunakan:
#
# - yt-dlp
# - os
# - sys
# - platform
#
# Cara install modul:
#
# - yt-dlp: pip install yt-dlp
#---------------------------------------------------------------------
# Catatan: Program ini memerlukan tools ffmpeg untuk menggabungkan
# audio dan video. Jika belum terinstall, silahkan install terlebih
# dahulu.
#---------------------------------------------------------------------

if platform.system() == "Windows":
    os.system("cls")
else:
    os.system("clear")

banner = """
██╗   ██╗████████╗██████╗ ██╗
╚██╗ ██╔╝╚══██╔══╝██╔══██╗██║
 ╚████╔╝    ██║   ██║  ██║██║
  ╚██╔╝     ██║   ██║  ██║██║
   ██║      ██║   ██████╔╝███████╗
   ╚═╝      ╚═╝   ╚═════╝ ╚══════╝

Youtube Video Downloader
Dibuat oleh: Rofi (Fixploit03)
"""

print(banner)

url_yt = input("[*] Masukkan URL Youtube: ").strip()
lokasi_simpan = input("[*] Masukkan lokasi penyimpanan: ").strip()

if not os.path.exists(lokasi_simpan):
    print("[-] Lokasi penyimpanan tidak ditemukan.")
    sys.exit(1)

nanya_resolusi = input("[?] Mau download video dengan resolusi terbaik (y/n): ").lower()

if nanya_resolusi == "y":
    print("[*] Mendownload video dengan resolusi terbaik...")
    try:
        ydl_opts = {
            'format': 'bestvideo+bestaudio/best',
            'outtmpl': os.path.join(lokasi_simpan, '%(title)s.%(ext)s'),
            'merge_output_format': 'mp4',
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url_yt])
        print("[+] Selesai.")
        sys.exit(0)
    except Exception as e:
        print(f"[-] Terjadi kesalahan: {e}")
        sys.exit(1)

elif nanya_resolusi == "n":
    print("\n[*] Mendapatkan resolusi video...")
    try:
        os.system(f"yt-dlp -F {url_yt}")
        
        id_video = input("Masukkan ID video: ").strip()
        print(f"[*] Mendownload video dengan ID: {id_video}...")
        
        ydl_opts = {
            'format': id_video,
            'outtmpl': os.path.join(lokasi_simpan, '%(title)s.%(ext)s'),
            'merge_output_format': 'mp4',
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url_yt])
        print("[+] Selesai.")
        sys.exit(0)
    except Exception as e:
        print(f"[-] Terjadi kesalahan: {e}")
        sys.exit(1)

else:
    print("[-] Masukkan tidak valid.")
    sys.exit(1)
