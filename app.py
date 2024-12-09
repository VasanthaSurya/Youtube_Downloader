from flask import Flask, render_template, request, url_for, redirect
import yt_dlp
import re

app = Flask(__name__)

def sanitize_filename(name: str) -> str:
    return re.sub(r'[<>:"/\\|?*]', '_', name)

def get_info(url):
    try:
        with yt_dlp.YoutubeDL({'quiet': True}) as ydl:
            info = ydl.extract_info(url, download=False)
    except Exception:
        pass
    return info

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        url = request.form['url']
        info = get_info(url)
        if 'entries' in info:
            return render_template('playlist.html', info=info['entries'])
        else:
            # return render_template('video.html', url=url)
            return export_formats(url)
            # return url_for('video', url=url)

    return render_template('index.html')

@app.route('/downloading', methods=['GET', 'POST'])
def download(url, f_id):
    # format_idx = request.form['format_idx']
    # url = request.form['url']
    ydl_opts = {
        'format': f_id + "+bestaudio",
        'quiet': False,
        'merge_output_format': 'mp4',
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])

def export_formats(url: str):
    info = get_info(url)
    filtered_formats = []
    for i in range(len(info["formats"])):
        if 'ext' in info["formats"][i].keys() and info["formats"][i].get('ext') == 'mp4':
            if info["formats"][i].get('height') in [1080, 720, 480]:
                filtered_formats.append(info["formats"][i])
    return render_template('video.html', info=filtered_formats, url=url, title=info.get('title'))


if __name__ == '__main__':
    app.run(debug=True)
