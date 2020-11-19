import mimetypes
import os
import sqlite3

import aiosql
from flask import Flask, render_template
from flask_mobility import Mobility

# Get db conn ready
from top_cat import THIS_SCRIPT_DIR, get_config

db_file_loc = os.path.expanduser(get_config()["DB_FILE"])
# We're just reading... so I think it's safe to share the connection on multiple threads
conn = sqlite3.connect(db_file_loc, check_same_thread=False)
conn.row_factory = sqlite3.Row
QUERIES = aiosql.from_path(THIS_SCRIPT_DIR + "/sql", "sqlite3")

# Got some great tips from https://blog.miguelgrinberg.com/post/the-flask-mega-tutorial-part-ii-templates

app = Flask(__name__)
Mobility(app)


@app.route("/")
@app.route("/index")
def index():
    return render_template("index.html")


# Just fetch the most recent 10 top posts
@app.route("/top/<string:label>")
def show_subpath(label):
    title = f"Top {label}"
    posts = QUERIES.get_top_posts_for_flask(conn, label)
    # We need to know if the url is for a video or a picture!
    posts = [
        {**post, "type": mimetypes.guess_type(post["media"])[0].split("/")[0]}
        for post in posts
    ]
    return render_template("top-post.html", title=title, posts=posts, label=label)
