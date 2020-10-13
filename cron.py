#!/usr/bin/env python3

import os
import sys
import subprocess as sp
from tempfile import NamedTemporaryFile
import datetime

from top_cat import get_config, THIS_SCRIPT_DIR

log_file_path = os.path.expanduser(f'~/top_cat_logs/{str(datetime.date.today())}/{str(datetime.datetime.now().time())[:8]}')

sp.call(f'mkdir -p "{os.path.dirname(log_file_path)}"' , shell=True)

execution = sp.run( [f'{THIS_SCRIPT_DIR}/top_cat.py', '-v']
                    , stderr=sp.STDOUT
                    , stdout=sp.PIPE
                )

open(log_file_path, 'a').write(execution.stdout.decode("utf-8"))

if execution.returncode:
    # Yell about it

    import requests
    import toml

    slack_payload = {
        "token": get_config()['SLACK_API_TOKEN'],
        "channel": '#derps',
        "text": execution.stdout.decode("utf-8"),
        "username": "TopCatRunner",
        "as_user": "TopCatRunner",
    }
    requests.get('https://slack.com/api/chat.postMessage', params=slack_payload)
