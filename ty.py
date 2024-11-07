import yt_dlp
import re
import os
import sys


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

    def set_videos(self, videos):
        self.videos = videos

    def get_videos(self):
        return self.videos

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

        return data

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

def sanitize_filename(name):
    return re.sub(r'[<>:"/\\|?*]', '_', name)

def download(url, format_id, video_number, save_dir, title):
    sanitized_title = sanitize_filename(title)
    ydl_opts = {
        'format': format_id + "+bestaudio",  # Merge the best audio with selected video format
        'quiet': False,
        'merge_output_format': 'mp4',  # Output format for merged files
        'outtmpl': os.path.join(save_dir, f"{video_number:02d}_{sanitized_title}.%(ext)s")  # Add index before sanitized title
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])

def check_format_availability(url, format_id):
    ydl_opts = {
        'quiet': True,
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)
        formats = [fmt['format_id'] for fmt in info['formats']]
    return format_id in formats

def list_playlist_videos(url, info):

    print("\nPlaylist contents:")
    for idx, entry in enumerate(info['entries'], start=1):
        print(f"{idx}. {entry['title']}")

    return info.get('entries')

def download_video(url, format_id, save_dir, idx, title):

    sanitized_title = sanitize_filename(title)
    ydl_opts = {
        'format': format_id + "+bestaudio",  # Merge the best audio with selected video format
        'quiet': False,
        'merge_output_format': 'mp4',  # Output format for merged files
        'outtmpl': os.path.join(save_dir, f"{idx:02d}_{sanitized_title}.%(ext)s")  # Add index before sanitized title
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])


def get_videos_to_download():

    try:
        videos_to_download = []
        videos = input("Enter index of video download. \nEnter comma separated values and range. \nEg: 1,2,3-7,12\n")
        for i in videos.split(','):
            if '-' in i:
                start, end = map(int, i.split('-'))
                videos_to_download.extend(range(start, end+1))
            elif not i:
                continue
            else:
                videos_to_download.append(int(i.strip()))
    except Exception as e:
        print(f"Exception in retrieving videos.\n{e}")
    finally:
        return videos_to_download


if __name__ == "__main__":
    g = Get()
    g.set_url()
    data_object = g.extract_info()

    if data_object.playlist:
        data_object.videos = list_playlist_videos(data_object.get_info())
    else:
        data_object.videos = [{'url':data_object.info.get('original_url')}]

    to_download = get_videos_to_download()
    selected_videos = [video['url'] for video in data_object.videos]
    print("\nSelect a resolution for all videos:")
    formats = get_formats(selected_videos[0])
    if formats:
        format_id = input("Enter the format ID you wish to download: ")
    else:
        print("No suitable formats found.")
    
    skipped_videos = []
    for idx, video_url in enumerate(selected_videos, start=1):
        video_title = data_object.videos[idx - 1]['title']
        print(f"\nChecking format availability for {video_title}...")

        # Check if the selected format is available for the video
        if check_format_availability(video_url, format_id):
            print(f"Downloading {video_title} in format {format_id}...")
            download_video(video_url, format_id, os.getcwd(), idx, video_title)
        else:
            print(f"Skipped {video_title}: Requested format {format_id} is not available.")
            skipped_videos.append((video_url, video_title, idx))  # Store skipped videos

    if skipped_videos:
        print("\nSome videos were skipped due to unavailable format.")
        retry = input(
            "Would you like to choose a new format for the skipped videos? (yes/no): ").strip().lower() == 'yes'
        if retry:
            for video_url, video_title, idx in skipped_videos:
                print(f"\nAvailable formats for {video_title}:")
                formats = get_formats(video_url)
                if formats:
                    new_format_id = input(f"Enter the format ID for {video_title}: ")
                    if check_format_availability(video_url, new_format_id):
                        print(f"Retrying download for {video_title} with format {new_format_id}...")
                        download_video(video_url, new_format_id, os.getcwd(), idx, video_title)
                    else:
                        print(f"Format {new_format_id} is still not available for {video_title}. Skipping.")
                else:
                    print(f"No available formats for {video_title}.")
