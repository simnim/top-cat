# Preamble:
The goal is really just to automate finding cute cat pictures. Enjoy.
This project is just for fun. It has no business prospects. It's not enterprise grade (tm).

# Purpose:
The purpose of this repo is to find the top cat picture at the moment at /r/aww
The project aims to enable:
* Via a cron job, run top_cat.py to query /r/aww every hour and use image classification apis (or libraries) to find the top cat picture at the time.
* Store entries in a db so we can look at things over time and memoize api responses (saving $$$$$$ and making re-running the script a bunch of times in a row sane and logical.)
* Push these pictures to a slack channel so you can always get a peek at the latest top_cat without ever visiting /r/aww. Bonus: Slack also acts as a nice recording of top cat history so you always have a nice high quality list of cat pictures to choose from even months later, by which time reddit may have made it hard to find these lost gems.
* "Secret" bonus: you can also ask for dog pictures instead, just edit the config file.

# Setup:
Get your google vision api access account setup and install the credentials on your machine.
aka google `GOOGLE_APPLICATION_CREDENTIALS`

`pip install --upgrade google-api-python-client requests oauth2client`

optional setup, but highly recommended:
Create a slack team, a `#top_cat` channel, and generate an api token @ https://api.slack.com/custom-integrations/legacy-tokens
(At the time that I originally figured out slack integrations this was the standard way. It still works, but maybe some day I'll swap it out when they get rid of it because "legacy".)

`~/.top_cat.json`:
This optional config file holds settings for the program. Check out `top_cat_example_config` for an example file

# Usage:
Run `./top_cat.py` as often as you like. It'll only query the google vision api once per image. Similarly, it'll also only post an image to slack once (if you've enabled that feature.)

# Notes:
I didn't bother with option parsing because it's supposed to be CRON centric (and because it'd be more work.) I might add option parsing if I expand this to also use other image labelling algorithms and want to play with it more interactively, but it's not worth it this second.

# See also:
https://github.com/fchollet/deep-learning-models (un?)fortunately google's vision api is currently faster and more accurate from my experience, so I didn't bother pursuing it, but check out some of the scripts in that repo for an interesting afternoon.
