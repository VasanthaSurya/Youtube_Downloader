import yt_dlp
import os
import re


def sanitize_filename(name):
    # Remove or replace invalid characters in filenames
    return re.sub(r'[<>:"/\\|?*]', '_', name)


def list_formats(url):
    ydl_opts = {
        'quiet': True,
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)

    print("\nAvailable formats (480p, 720p, 1080p):")
    filtered_formats = [
        fmt for fmt in info['formats']
        if fmt.get('height') in [480, 720, 1080]  # Only 480p, 720p, or 1080p
    ]

    for fmt in filtered_formats:
        format_id = fmt.get('format_id')
        resolution = fmt.get('resolution')
        file_size = fmt.get('filesize')  # in bytes
        size_in_mb = f"{file_size / (1024 * 1024):.2f} MB" if file_size else "Unknown size"
        print(f"{format_id}: {resolution}, {size_in_mb}")

    return filtered_formats


def check_format_availability(url, format_id):
    ydl_opts = {
        'quiet': True,
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)
        formats = [fmt['format_id'] for fmt in info['formats']]
    return format_id in formats


def list_playlist_videos(url):
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

    return info.get('entries', []), info.get('title', 'Playlist')


def download_video(url, format_id, save_dir, idx, title):
    # Sanitize title for filename
    sanitized_title = sanitize_filename(title)
    ydl_opts = {
        'format': format_id + "+bestaudio",  # Merge the best audio with selected video format
        'quiet': False,
        'merge_output_format': 'mp4',  # Output format for merged files
        'outtmpl': os.path.join(save_dir, f"{idx:02d}_{sanitized_title}.%(ext)s")  # Add index before sanitized title
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])


class Download:
    def __init__(self):
        self.down_dir = "yt_dlp_Downloads"
        self.home = "E:\\"
        self.move_to_home()

    def move_to_home(self):
        os.chdir(self.home)
        if not os.path.exists(os.path.join(self.home, self.down_dir)):
            os.mkdir(self.down_dir)

    def main(self, url):
        # Step 1: List videos in the playlist and get playlist title for folder name
        playlist_videos, playlist_title = list_playlist_videos(url)
        if not playlist_videos:
            return

        # Sanitize playlist title for directory name
        playlist_dir = os.path.join(self.down_dir, sanitize_filename(playlist_title))
        if not os.path.exists(playlist_dir):
            os.mkdir(playlist_dir)

        # Step 2: Choose download option - all videos or specific ones
        download_all = input("Do you want to download all videos in the playlist? (yes/no): ").strip().lower() == 'yes'
        if download_all:
            selected_videos = [video['url'] for video in playlist_videos]
        else:
            video_indices = input("\nEnter video numbers to download (comma-separated, e.g., 1,3,5): ")
            selected_videos = [playlist_videos[int(i) - 1]['url'] for i in video_indices.split(",") if i.isdigit()]

        # Step 3: Choose the format for all videos
        print("\nSelect a resolution for all videos:")
        formats = list_formats(selected_videos[0])
        if formats:
            format_id = input("Enter the format ID you wish to download: ")
        else:
            print("No suitable formats found.")
            return

        # Step 4: Download each video in the selected format and save with numbered index
        skipped_videos = []
        for idx, video_url in enumerate(selected_videos, start=1):
            video_title = playlist_videos[idx - 1]['title']
            print(f"\nChecking format availability for {video_title}...")

            # Check if the selected format is available for the video
            if check_format_availability(video_url, format_id):
                print(f"Downloading {video_title} in format {format_id}...")
                download_video(video_url, format_id, playlist_dir, idx, video_title)
            else:
                print(f"Skipped {video_title}: Requested format {format_id} is not available.")
                skipped_videos.append((video_url, video_title, idx))  # Store skipped videos

        # Step 5: Retry download for skipped videos with new format selection
        if skipped_videos:
            print("\nSome videos were skipped due to unavailable format.")
            retry = input(
                "Would you like to choose a new format for the skipped videos? (yes/no): ").strip().lower() == 'yes'
            if retry:
                for video_url, video_title, idx in skipped_videos:
                    print(f"\nAvailable formats for {video_title}:")
                    formats = list_formats(video_url)
                    if formats:
                        new_format_id = input(f"Enter the format ID for {video_title}: ")
                        if check_format_availability(video_url, new_format_id):
                            print(f"Retrying download for {video_title} with format {new_format_id}...")
                            download_video(video_url, new_format_id, playlist_dir, idx, video_title)
                        else:
                            print(f"Format {new_format_id} is still not available for {video_title}. Skipping.")
                    else:
                        print(f"No available formats for {video_title}.")


if __name__ == "__main__":
    link = "https://youtube.com/playlist?list=PLBlnK6fEyqRjSgal6OIEfzK4upXvkHSxW&feature=shared"
    obj = Download()
    obj.main(link)
