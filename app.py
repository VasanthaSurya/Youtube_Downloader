from flask import Flask, render_template, request, redirect, url_for
import yt_dlp

app = Flask(__name__)

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        url = request.form['url']
        with yt_dlp.YoutubeDL({'quiet': True}) as ydl:
            info = ydl.extract_info(url, download=False)
        if 'entries' in info:
            return render_template('playlist.html', info=info['entries'])
        else:
            return render_template('video.html', info=info)
    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True)
