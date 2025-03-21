## Cara Instal

Berikut ini adalah langkah-langkah untuk menginstal YTDL:

## Persyaratan

YTDL memerlukan beberapa persyaratan, di antaranya sebagai berikut:

- Python 3.x
- Git
- Ffmpeg

### 1. Windows

> Pastikan semua persyaratan diatas sudah terinstal di Windows Anda, jika belum terinstal bisa mengunduhnya disini:
>
> - Python 3.x [Link](https://www.python.org/ftp/python/3.13.2/python-3.13.2-amd64.exe)
> - Git [Link](https://github.com/git-for-windows/git/releases/download/v2.48.1.windows.1/Git-2.48.1-64-bit.exe)
> - Ffmpeg [Link](https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip)

Buka CMD dan ketikkan printah dibawah ini:

```
$ git clone https://github.com/fixploit03/ytdl.git
$ cd ytdl
$ python -m venv .modules
$ .modules\Scripts\activate.bat
$ pip3 install -r requirements.txt
```

### 2. Linux (Ubuntu/Debian)

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
$ pip3 install -r requirements.txt
```

<div align="left">
  [ <a href="https://github.com/fixploit03/ytdl">Beranda</a> ]
</div>
