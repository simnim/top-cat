#!/usr/bin/env python3

import os
import re
import subprocess as sp
import sys
from datetime import datetime

import requests

from top_cat import THIS_SCRIPT_DIR, get_config

config = get_config()

log_file_prefix = os.path.expanduser(
    f"~/top_cat_logs/{str(datetime.today())}/{str(datetime.now().time())[:8]}"
)


# Gather stats from ps. This should work on mac and linux.
# Not certain date regex workes in all locales.
## Mon Jul 19 08:34:39 2021         1 /sbin/launchd
running_procs = [
    re.match(
        r"(.+\s+.+\s+.+\s+.+\s+[^\s]+)\s+(\d+)\s+(.*)", line, flags=re.M | re.S
    ).groups()
    for line in sp.check_output("ps -a -x -o lstart,pid,command", shell=True)
    .decode("utf-8")
    .split("\n")
]

# If top_cat.py has been running too long, then we'll kill previous proc and end early.
# If it's just taking a few cron cycles, we'll wait a bit longer
top_cat_ps_rows = [row for row in running_procs if "top_cat.py" in row[-1]]
top_cat_ps_row = (top_cat_ps_rows or [None])[0]
if top_cat_ps_row:
    how_long_still_running = (
        datetime.strptime(top_cat_ps_row[0], "%c") - datetime.now()
    ).total_secons()
    if how_long_still_running > int(config["MAX_TOP_CAT_CRON_RUNTIME"]):
        print(
            f"trying to kill old top-cat proc {top_cat_ps_row[1]}, was running for {how_long_still_running} seconds",
            file=sys.stderr,
        )
        os.kill(top_cat_ps_row[1], 9)
    sys.exit()

# Run top-cat and catch possible errors.
sp.call(f'mkdir -p "{os.path.dirname(log_file_prefix)}"', shell=True)
execution = sp.run(
    [f"{THIS_SCRIPT_DIR}/top_cat.py", "-v"], stderr=sp.STDOUT, stdout=sp.PIPE
)

# Write log file
log_file_path = log_file_prefix + "_" + str(datetime.now().time())[:8]
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
