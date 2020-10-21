from top_cat import *
import pytest
from contextlib import contextmanager
import subprocess as sp
import time


# https://docs.python.org/3/library/contextlib.html
@contextmanager
def flask_app_server():
    # Run the flask app
    flask_proc = sp.Popen(
          ['flask','run']
        , stdout=sp.PIPE
        , stderr=sp.PIPE
      )
    time.sleep(1)
    try:
        yield flask_proc
    finally:
        flask_proc.kill()

def test_flask_app_index():
    import requests
    with flask_app_server() as flask_app:
        req = requests.get('http://127.0.0.1:5000')
        # Make sure the index page loads and that it advertises my github
        assert req.ok and 'https://github.com/simnim/top-cat' in req.text

def test_flask_app_top_cat():
    import requests
    with flask_app_server() as flask_app:
        req = requests.get('http://127.0.0.1:5000/top/cat')
        # Load top/cat and check that we got some cats
        assert req.ok and len(re.findall('<hr>', req.text)) > 2

def test_flask_server_runs_at_all():
    with flask_app_server() as flask_app:
        if flask_app.poll() is not None:
            print(flask_app.stderr.read().decode('utf-8'),file=sys.stderr)
        assert flask_app.poll() is None
