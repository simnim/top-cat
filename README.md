# Purpose:
Automate finding cute cat and dog pictures from /r/aww and remember them forever. Enjoy.
This project is just for fun. It has no business prospects. It's not enterprise grade (tm).

Check #FIXME for the latest top cat on /r/aww

# Install

## Optional but encouraged:

* Install pyenv and pyenv-virtualenv
* Create an environment for this project

## Required steps

```bash
## Optional steps:
# In case you haven't done so check it out and cd into the repo dir
mkdir -p ~/git
cd ~/git
git checkout https://github.com/simnim/top_cat.git
cd top_cat

# If you want to use pyenv-virtualenv this sets it up for you
pyenv install 3.8.5
pyenv virtualenv 3.8.5 top-cat
pyenv local top-cat

## /Optional steps

## Required steps:

# Either way make sure you have the necessary packages installed
pip install -r requirements.txt

# Set up your config so you can post to slack
mkdir -p ~/.top_cat
cd ~/.top_cat
$EDITOR config.toml

# ok, now you should be good to go on running the app and finding cats and dogs
cd ~/git/top_cat

# Run it
./top_cat.py -v
```

## You can also set up CRON to call it every 5 mins instead


# Config file
`~/.top_cat/config.toml`:
This optional config file holds settings for the program. Check out `top_cat_default.toml` for settings and an explanation of each variable


### optional setup, but highly recommended:
Create a slack team, a `#top_cat` channel, and generate an api token @ https://api.slack.com/custom-integrations/legacy-tokens
(At the time that I originally figured out slack integrations this was the standard way. It still works, but maybe some day I'll swap it out when they get rid of it because "legacy".)

### How I made the facebook page:
I followed this guide http://nodotcom.org/python-facebook-tutorial.html to get everything set up. I needed to get a facebook page_access_token so I could post to the page. I also needed the help of the following pages to get it all working: https://developers.facebook.com/tools/explorer/ https://developers.facebook.com/tools/debug/accesstoken/ https://developers.facebook.com/apps



# Usage:
Run `./top_cat.py` as often as you like. It'll only query the google vision api once per image. Similarly, it'll also only post an image to slack once (if you've enabled that feature.)
