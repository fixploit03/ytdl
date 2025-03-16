# YTDL

Program python sederhana untuk mendownload video dari Youtube.

## Persyaratan

- Python
- Git
- Ffmpeg

## Cara Instal


### 1. Termux

Buka aplikasi Termux dan ketikkan perintah dibawah ini:

```
$ pkg update
$ pkg install python3
$ pkg install ffmpeg
$ pkg install git
$ git clone https://github.com/fixploit03/ytdl.git
$ cd ytdl
$ python3 -m venv .modules
$ source .modules/bin/activate
$ pip3 install yt-dlp
```

### 2. Windows

> Pastikan semua persyaratan diatas sudah terinstal di Windows Anda, jika belum terinstal bisa mengunduhnya disini:
>
> - Python [Link](https://www.python.org/ftp/python/3.13.2/python-3.13.2-amd64.exe)
> - Git [Link](https://github.com/git-for-windows/git/releases/download/v2.48.1.windows.1/Git-2.48.1-64-bit.exe)
> - Ffmpeg [Link](https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip)

Buka CMD dan ketikkan printah dibawah ini:

```
$ git clone https://github.com/fixploit03/ytdl.git
$ cd ytdl
$ python -m venv .modules
$ .modules\Scripts\activate.bat
$ pip3 install yt-dlp
```

### 3. Linux (Ubuntu/Debian)

Buka terminal dan ketikkan perintah dibawah ini:

```
$ sudo apt-get update
$ sudo apt-get install python3
$ sudo apt-get install python3-pip
$ sudo apt-get install python3-venv
$ sudo apt-get install ffmpeg
$ sudo apt-get install git
$ git clone https://github.com/fixploit03/ytdl.git
$ cd ytdl
$ python3 -m venv .modules
$ source .modules/bin/activate
$ pip3 install yt-dlp
```

## Run

Pastikan berada di dalam folder yang berisi file `ytdl.py`, dan pastikan `venv` atau virtual environmentnya diaktifkan dulu sebelum menjalankan program dengan mengetikkan `source .modules/bin/activate`.

Untuk menjalankan programnya ketikkan perintah dibawah ini:

```
python3 ytdl.py
```

> Kalo di Windows ga usah pake angka 3 langsung aja `python ytdl.py`
