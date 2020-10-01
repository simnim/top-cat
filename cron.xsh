#!/usr/bin/env xonsh

import os
import sys

THIS_SCRIPT_DIR = os.path.dirname(os.path.realpath(os.path.join(os.getcwd(), os.path.expanduser(__file__))))

execution = !(@(THIS_SCRIPT_DIR)/top_cat.py -v 2>&1 )

# For some reason I need to peek at this to get the output... bug?
execution.returncode

open(os.path.expanduser('~/top_cat_log'),'a').write(str(execution.output))

if execution.returncode:
    # Yell about it

    import requests
    import toml

    slack_payload = {
        "token": toml.load(os.path.expanduser('~/.top_cat/config.toml'))['SLACK_API_TOKEN'],
        "channel": '#derps',
        "text": str(execution.output),
        "username": "TopCatRunner",
        "as_user": "TopCatRunner",
    }
    requests.get('https://slack.com/api/chat.postMessage', params=slack_payload)
