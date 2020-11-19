#!/usr/bin/env python3

import datetime
import os

# import sys
import subprocess as sp

import requests

from top_cat import THIS_SCRIPT_DIR, get_config

config = get_config()

log_file_path = os.path.expanduser(
    f"~/top_cat_logs/{str(datetime.date.today())}/{str(datetime.datetime.now().time())[:8]}"
)

sp.call(f'mkdir -p "{os.path.dirname(log_file_path)}"', shell=True)

execution = sp.run(
    [f"{THIS_SCRIPT_DIR}/top_cat.py", "-v"], stderr=sp.STDOUT, stdout=sp.PIPE
)

open(log_file_path, "a").write(execution.stdout.decode("utf-8"))

# Complain about errors if necessary
if execution.returncode:
    slack_payload = {
        "token": config["SLACK_API_TOKEN"],
        "channel": "#derps",
        "text": execution.stdout.decode("utf-8"),
        "username": "TopCatRunner",
        "as_user": "TopCatRunner",
    }
    requests.get("https://slack.com/api/chat.postMessage", params=slack_payload)
