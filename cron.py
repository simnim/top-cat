#!/usr/bin/env python3

import datetime
import os
import subprocess as sp
import sys

import requests

from top_cat import THIS_SCRIPT_DIR, get_config

config = get_config()

log_file_prefix = os.path.expanduser(
    f"~/top_cat_logs/{str(datetime.date.today())}/{str(datetime.datetime.now().time())[:8]}"
)

# Exit early if top_cat was already running before this started.
running_procs = sp.check_output("ps aux", shell=True).decode("utf-8")
if len([line for line in running_procs.split("\n") if "top_cat.py" in line]) > 0:
    sys.exit()

sp.call(f'mkdir -p "{os.path.dirname(log_file_prefix)}"', shell=True)

execution = sp.run(
    [f"{THIS_SCRIPT_DIR}/top_cat.py", "-v"], stderr=sp.STDOUT, stdout=sp.PIPE
)

log_file_path = log_file_prefix + "_" + str(datetime.datetime.now().time())[:8]
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
