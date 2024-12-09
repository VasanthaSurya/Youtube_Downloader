from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict
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

    def set_url(self, url: str):
        self.url = url

    def get_url(self) -> str:
        return self.url

    def set_info(self, info: Dict):
        self.info = info

    def get_info(self) -> Dict:
        return self.info

    def set_videos(self, videos: Dict):
        self.videos = videos

    def get_videos(self) -> Dict:
        return self.videos

    def set_playlist_status(self, status):
        self.playlist = status

    def get_playlist_status(self):
        return self.playlist


class Get:
    def __init__(self):
        self.url = ''

    def set_url(self)-> None:
        self.url = input("Enter URL: ")

    @staticmethod
    def is_playlist(info: Dict):
        if info.get('entries'):
            return True
        return False

    def extract_info(self) -> Data:
        options = {
            'quiet': True
        }
        try:
            with yt_dlp.YoutubeDL(options) as ydl:
                info = ydl.extract_info(self.url, download=False)

            data = Data()
            data.set_url(self.url)
            data.set_info(info)
            data.set_playlist_status(self.is_playlist(info))

        except Exception as invalid_url:
            print(f"Invalid Url: {invalid_url}")
            sys.exit(0)

        return data


def extract_video_info(url: str) -> Dict:
    options = {
        'quiet': True
    }
    try:
        with yt_dlp.YoutubeDL(options) as ydl:
            info = ydl.extract_info(url, download=False)
    except Exception as invalid_url:
        print(f"Invalid Url: {invalid_url}")
        sys.exit(0)

    return info


def get_formats(info: Dict) -> List:
    print("\nAvailable formats:")
    filtered_formats = []
    for i in range(len(info["formats"])):
        if 'ext' in info["formats"][i].keys() and info["formats"][i].get('ext') == 'mp4':
            if info["formats"][i].get('height') in [1440, 2160,1080, 720, 480] or info['formats'][i].get('quality') in ['360', '720', '1080']:
                filtered_formats.append(info["formats"][i])
                f_id = info["formats"][i].get('format_id')
                resolution = info["formats"][i].get('resolution')
                file_size = info["formats"][i].get('filesize')  # in bytes
                size_in_mb = f"{file_size / (1024 * 1024):.2f} MB" if file_size else "Unknown size"
                print(f"{f_id}: {resolution}, {size_in_mb}")

    return filtered_formats


def sanitize_filename(name: str) -> str:
    return re.sub(r'[<>:"/\\|?*]', '_', name)


def check_format_availability(url: str, frmt_id: str) -> bool:
    ydl_opts = {
        'quiet': True,
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)
    return frmt_id in [fmt['format_id'] for fmt in info['formats']]


# def list_playlist_videos(info: Dict) -> Dict:
#     """

#     :param info: Dict
#     :return :

#     return type is a dictionary with keys as index and values is another dictionary
#     """
#     print("\nPlaylist contents:")
#     video_data = {}
#     for i, entry in enumerate(info['entries'], start=1):
#         print(f"{i}. {entry['title']}")
#         video_data[i] = extract_video_info(entry['original_url'])

#     return video_data
def list_playlist_videos(info: Dict) -> Dict:
    """

    :param info: Dict
    :return :

    return type is a dictionary with keys as index and values is another dictionary
    """

    def extract_video_data(i, entry):
        return i, extract_video_info(entry['original_url'])

    print("\nPlaylist contents:")
    video_data = {}

    with ThreadPoolExecutor() as executor:
        futures = []
        for i, entry in enumerate(info['entries'], start=1):
            print(f"{i}. {entry['title']}")
            print(f"Thread {i} started")
            futures.append(executor.submit(extract_video_data, i, entry))
        
        for future in as_completed(futures):
            try:
                i, data = future.result()
                print(f"Thread {i} Ended.")
                video_data[i] = data
            except Exception as te:
                print(f"Error fetching data for video {i}: {te}")

    return video_data

def download_video(url: str, format_idx, save_dir, video_number, title) -> None:
    """
    :type url: str
    :type format_idx: str
    :type save_dir: str
    :type video_number: int
    :type title: str
    """
    sanitized_title = sanitize_filename(title)
    ydl_opts = {
        'format': format_idx + "+bestaudio",
        'quiet': False,
        'merge_output_format': 'mp4',
        'outtmpl': os.path.join(save_dir, f"{video_number:02d}_{sanitized_title}.%(ext)s")
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])


def get_videos_to_download(folder: bool) -> List:
    if not folder:
        return [0]
    videos_to_download = []
    try:
        videos = input("Enter index of video download. \nEnter comma separated values and range. \nEg: 1,2,3-7,12\n")
        for i in videos.split(','):
            if '-' in i:
                start, end = map(int, i.split('-'))
                videos_to_download.extend(range(start, end + 1))
            elif not i:
                continue
            else:
                videos_to_download.append(int(i.strip()))
    except Exception as e:
        print(f"Exception in retrieving videos.\n{e}")
    finally:
        return videos_to_download

def main():

    g = Get()
    g.set_url()
    data_object = g.extract_info()

    if data_object.playlist:
        data_object.videos = list_playlist_videos(data_object.get_info())
    else:
        temp = data_object.info
        temp['url'] = data_object.info.get('original_url')
        data_object.videos = [temp]
        del temp

    to_download = get_videos_to_download(data_object.playlist)
    selected_videos = [data_object.videos[i] for i in to_download]
    print("\nSelect a resolution for video:")

    formats = get_formats(selected_videos[0])

    if formats:
        format_id = input("Enter the format ID you wish to download: ")
        try:
            int(format_id)
        except ValueError as v:
            print(f"Invalid Format, {v}")
            sys.exit(0)
    else:
        print("No suitable formats found.")
        sys.exit(0)

    skipped_videos = []
    for idx, video_url in enumerate(selected_videos, start=1):
        video_title = data_object.videos[idx-1]['title']
        print(f"\nChecking format availability for {video_title}...")

        # Check if the selected format is available for the video
        if check_format_availability(video_url.get('original_url'), format_id):
            print(f"Downloading {video_title} in format {format_id}...")
            download_video(video_url.get('original_url'), format_id, os.getcwd(), idx, video_title)
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
                    if check_format_availability(video_url.get('original_url'), new_format_id):
                        print(f"Retrying download for {video_title} with format {new_format_id}...")
                        download_video(video_url, new_format_id, os.getcwd(), idx, video_title)
                    else:
                        print(f"Format {new_format_id} is still not available for {video_title}. Skipping.")
                else:
                    print(f"No available formats for {video_title}.")

if __name__ == "__main__":
    main()