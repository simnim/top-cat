from flask import Flask
from flask import render_template
import mimetypes
import sqlite3
import aiosql
import os

# Get db conn ready
from top_cat import get_config
db_file_loc = os.path.expanduser(get_config()['DB_FILE'])
print(db_file_loc)
# We're just reading... so I think it's safe to share the connection on multiple threads
conn = sqlite3.connect(db_file_loc, check_same_thread=False)
conn.row_factory = sqlite3.Row
queries = aiosql.from_path("sql", "sqlite3")

# Got some great tips from https://blog.miguelgrinberg.com/post/the-flask-mega-tutorial-part-ii-templates

app = Flask(__name__)

@app.route('/')
@app.route('/index')
def index():
    return render_template('index.html')

# Just fetch the most recent 10 top posts
@app.route('/top/<string:label>')
def show_subpath(label):
    title = f"Top {label}"
    posts = queries.get_top_posts(conn, label)
    # We need to know if the url is for a video or a picture!
    posts = [ {**post, 'type':mimetypes.guess_type(post['media'])[0].split('/')[0]} for post in posts]
    return render_template('top-post.html', title=title, posts=posts)

