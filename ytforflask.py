"""
User Stories
3. If playlist
3.1. Get Videos to download (in the format 1-5, 7, 9, ...)
3.2. Select resolution to download(formats)
3.3. Download videos

"""

import yt_dlp
import os
import sys
import re


class Data:
    def __init__(self):
        self.url = ''
        self.info = {}
        self.videos = {}
        self.playlist = False

    def set_url(self, url):
        self.url = url

    def get_url(self):
        return self.url

    def set_info(self, info):
        self.info = info

    def get_info(self):
        return self.info

    def get_videos(self):
        return self.videos

    def set_videos(self, videos):
        self.videos = videos

    def set_playlist_status(self, status):
        self.playlist = status

    def get_playlist_status(self):
        return self.playlist


class Get:
    def __init__(self):
        self.url = ''

    def set_url(self):
        self.url = input("Enter URL: ")

    def is_playlist(self, info):
        if info.get('entries') and isinstance(info.get('entries'), list):
            return True
        return False

    def extract_info(self):
        options = {
            'quiet': True
        }
        with yt_dlp.YoutubeDL(options) as ydl:
            info = ydl.extract_info(self.url, download=False)

        data = Data()
        data.set_url(self.url)
        data.set_info(info)
        data.set_playlist_status(self.is_playlist(info))

        return info


class GetLink:

    def __init__(self):
        self.url = ""
        self.playlist = False
        self.handler = None
        self.info = {}

    def get_url(self):
        self.url = input("Enter URL: ")
        self.extract()
        self.is_playlist()
        if not self.playlist:
            self.handler.download(self.info)

    def is_playlist(self):
        if self.info.get('entries') and isinstance(self.info.get('entries'), list):
            self.playlist = True
            self.handler = PlaylistDownloader()
        else:
            self.handler = VideoDownloader()

    @staticmethod
    def get_formats(info) -> list:

        print("\nAvailable formats:")
        filtered_formats = []
        for i in range(len(info["formats"])):
            if 'ext' in info["formats"][i].keys() and info["formats"][i].get('ext') == 'mp4':
                if info["formats"][i].get('height') in [1080, 720, 480]:
                    filtered_formats.append(info["formats"][i])

        for fmt in filtered_formats:
            format_id = fmt.get('format_id')
            resolution = fmt.get('resolution')
            file_size = fmt.get('filesize')  # in bytes
            size_in_mb = f"{file_size / (1024 * 1024):.2f} MB" if file_size else "Unknown size"
            print(f"{format_id}: {resolution}, {size_in_mb}")

        return filtered_formats

    @staticmethod
    def sanitize_filename(name):
        return re.sub(r'[<>:"/\\|?*]', '_', name)

    def extract(self):
        options = {
            'quiet': True
        }
        with yt_dlp.YoutubeDL(options) as ydl:
            self.info = ydl.extract_info(self.url, download=False)

        return self.info

    @staticmethod
    def check_format_availability(url, format_id):
        ydl_opts = {
            'quiet': True,
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)

        return format_id in [fmt['format_id'] for fmt in info['formats']]


class VideoDownloader:
    def __init__(self):
        self.format = None

    def select_format(self, info):
        formats = GetLink.get_formats(info)

        if self.format is None:
            self.format = input("Choose a format to download: ")

        return formats

    def download(self, info):
        self.select_format(info)
        sanitized_title = GetLink.sanitize_filename(info.get("title"))
        ydl_opts = {
            'format': self.format + "+bestaudio",
            'quiet': False,
            'merge_output_format': 'mp4',
            'outtmpl': f"{sanitized_title}.%(ext)s"
        }
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([info["webpage_url"]])
        except Exception as e:
            print(f"Something went wrong. Try looking for ...\n, {e}")
            exit(0)


class PlaylistDownloader:
    def __init__(self):
        self.retry = 0
        self.videos_to_download = []
        self.video_entries = []
        self.playlist_title = ''

    def get_videos_to_download(self):

        try:
            videos = input("Enter index of video download. \nEnter comma separated values and range. \nEg: 1,2,3-7,12\n")
            for i in videos.split(','):
                if '-' in i:
                    start, end = map(int, i.split('-'))
                    self.videos_to_download.extend(range(start, end+1))
                elif not i:
                    continue
                else:
                    self.videos_to_download.append(int(i.strip()))
        except Exception as e:
            print(f"Exception in retrieving videos.\n{e}")
        finally:
            self.retry += 1
            if self.retry == 3:
                print("Maximum tries reached. Please try again later.")
                sys.exit(0)
            if not self.videos_to_download:
                self.get_videos_to_download()
            else:
                return

    def list_playlist_videos(self, url):
        ydl_opts = {
            'quiet': True,
            'extract_flat': True  # Only list videos without downloading
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)

        if 'entries' in info:
            print("\nPlaylist contents:")
            for idx, entry in enumerate(info['entries'], start=1):
                print(f"{idx}. {entry['title']}")
        else:
            print("The provided URL is not a playlist.")

        self.video_entries, self.playlist_title = info.get('entries', []), GetLink.sanitize_filename(info.get('title', 'Playlist'))


    def download(self, url):
        self.list_playlist_videos(url)
        self.get_videos_to_download()

        if not os.path.exists(self.playlist_title):
            os.mkdir(self.playlist_title)

        selected_videos = [self.video_entries[int(i) - 1]['url'] for i in self.videos_to_download]

        print("\nSelect a resolution for all videos:")
        formats = GetLink.get_formats(info)
        if formats:
            format_id = input("Enter the format ID you wish to download: ")
        else:
            print("No suitable formats found.")
            return



if __name__ == "__main__":
    obj = GetLink()
    obj.get_url()
