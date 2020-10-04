#!/usr/bin/env python

import os
import sys
import subprocess as sp

from top_cat import get_config, THIS_SCRIPT_DIR

sp.call('mkdir -p $HOME/top_cat_logs/', shell=True)

execution = sp.run(f'''{THIS_SCRIPT_DIR}/top_cat.py -v 2>&1 \
                        | tee -a $HOME/top_cat_logs/$(date "+%Y-%m-%d")'''
                    , shell=True
                    , stderr=sp.STDOUT
                    , stdout=sp.PIPE
                )

if execution.returncode:
    # Yell about it

    import requests
    import toml

    slack_payload = {
        "token": get_config()['SLACK_API_TOKEN'],
        "channel": '#derps',
        "text": str(execution.output),
        "username": "TopCatRunner",
        "as_user": "TopCatRunner",
    }
    requests.get('https://slack.com/api/chat.postMessage', params=slack_payload)
