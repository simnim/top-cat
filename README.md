# Purpose:
Automate finding cute cat and dog pictures from /r/aww and remember them forever.
This project is just for fun. I'm not making any money from it.

If the top post on /r/aww has a cat in it, then it's a top cat, if it's got a dog, then it's a top dog. You can also customize what labels to look for with the user config file.

To see the outputs of this tool, check out my website @ http://topcat.app and click on "Top Cat" or "Top Dog" in the nav bar up top. Source code for my website is also available @ https://github.com/simnim/nh_website

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

Check out `default_config.toml` for settings and an explanation of each variable


# Available Computer Vision models:
For this project you can use one of two models I've configured or roll your own. This is configurable with the `MODEL_TO_USE` config option. The two I've made easy to use are deeplabv3 -> `deeplab.py` and google's vision api -> `gvision_labeler.py`. To roll your own, simply create another python file in the project directory and implement get_labelling_func_given_config (see default_config.toml for more details) then of course set `MODEL_TO_USE` to the name of your new file without the .py suffix.


## You can also set up CRON to call top_cat.py every 5 mins
`./top_cat.py` will only ever query the google vision api once per unique image/video url. Similarly, it'll also only post to slack once per new top cat/dog (if you set up slack integration)

```
*/5 * * * *   $HOME/git/top_cat/cron.py
```

# Optional extra setup:
## Add slack integration:
* Create an app @ https://api.slack.com/apps/
* [ OAuth & Permissions ] -> Add `chat:write` and `chat:write.customize` under Scopes
* [ OAuth & Permissions ] -> click [ Install App to Workplace ]
* ... requesting permission to access ... -> click [ Allow ]
* Copy paste your fresh token into your user config file @ `~/.top_cat/config.toml` (token looks like `xoxb-...`)


# How to run tests
```
# All tests
pytest

# Skip the slow tests (vision model tests)
pytest -k 'not slow'

# Skip tests that need an internet connection AND the slow tests
pytest -k 'not net and not slow'
```
