# Purpose:
Automate finding cute cat and dog pictures from /r/aww and remember them forever.
This project is just for fun. I'm not making any money from it.

If the top post has a cat in it, then it's a top cat, if it's got a dog, then it's a top dog. You can also customize what labels to look for with the user config file.

This project also comes with a flask app so you can browse the latest top cat and dog in a web browser! I'm hosting this app @ https://simnim.xyz/top/cat so feel free to check it out.

# Install

```bash
# In case you haven't done so check it out and cd into the repo dir
mkdir -p ~/git
cd ~/git
git clone https://github.com/simnim/top-cat.git
cd top-cat

## Optional steps:
# If you want to use pyenv-virtualenv this sets it up for you
pyenv install 3.8.5
pyenv virtualenv 3.8.5 top-cat
pyenv local top-cat
## /Optional steps

# Either way make sure you have the necessary packages installed
pip install -r requirements.txt

# Set up your config so you can post to slack
mkdir -p ~/.top_cat
cd ~/.top_cat
$EDITOR config.toml

# ok, now you should be good to go on running the app and finding cats and dogs
cd ~/git/top-cat

# Run it
./top_cat.py -v
```


# Set up your config file
`~/.top_cat/config.toml`:

Check out `top_cat_default.toml` for settings and an explanation of each variable



## You can also set up CRON to call top_cat.py every 5 mins
`./top_cat.py` will only ever query the google vision api once per unique image/video url. Similarly, it'll also only post to slack once per new top cat/dog (if you set up slack integration)

# Optional extra setup:
## Add slack integration:
* Create an app @ https://api.slack.com/apps/
* [ OAuth & Permissions ] -> Add `chat:write` and `chat:write.customize` under Scopes
* [ OAuth & Permissions ] -> click [ Install App to Workplace ]
* ... requesting permission to access ... -> click [ Allow ]
* Copy paste your fresh token into your user config file @ `~/.top_cat/config.toml` (token looks like `xoxb-...`)


# How to run tests
```
pytest
```

# How to run flask webserver
If you have python-dotenv installed you can just do `flask run` in the project dir, otherwise you can do `export FLASK_APP=serve_top_posts.py; flask run`  (Caveot: the navbar up top assumes you're processing top cat and top dog, but no other labels...)
