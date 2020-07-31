#!/usr/bin/env python

"""
Nick Hahner 2017-2020
Ever wanted to automate finding the top cute cat picture from /r/aww to send to your friends?
All you need to do is run ./top_cat.py and your life will change forever.

You'll need to create ~/.top_cat/config.toml if you want to find dogs instead!
You can also add your slack api key to ^ if you want a nifty slack integration.
All items in the config file are optional. See example config for defaults.

Usage:
    top_cat.py [options]

Options:
    -h, --help            Show this help message and exit
    -v, --verbose         Debug info
    -c, --config          config file location [default: ~/.top_cat/config.toml]
    -d, --db-file         sqlite3 db file location [default: ~/.top_cat/db]

"""

import requests
import re
import base64
# from googleapiclient import discovery
# from oauth2client.client import GoogleCredentials
# import facebook
import sys
import json
import toml
import sqlite3
import hashlib
import os
from time import sleep
from PIL import Image
from io import BytesIO, StringIO
from tempfile import NamedTemporaryFile

# Because the reddit api links use escaped html strings ie &amp;
from xml.sax.saxutils import unescape


from docopt import docopt

THIS_SCRIPT_DIR = os.path.dirname(os.path.realpath(__file__))
DEFAULT_CONFIG = toml.load(this_script_dir+'/top_cat_default.toml')


def get_config():
    user_config_file_loc = os.path.expanduser("~/.top_cat/config.toml")
    # Let's query the config file
    if os.path.isfile(user_config_file_loc):
        try:
            top_cat_user_config = toml.load(user_config_file_loc)
        except Exception as e:
            print( "Malformed config file at '%s'" % (config_file_loc) , file=sys.stderr)
            exit(1)
    else:
        top_cat_user_config = dict()

    top_cat_config = {**DEFAULT_CONFIG, **top_cat_user_config}

    # If we plan on posting to social media, let's make sure we have tokens to try
    assert ( not top_cat_config['POST_TO_SLACK_TF']
                or (top_cat_config['POST_TO_SLACK_TF'] and top_cat_config['SLACK_API_TOKEN'] and top_cat_config['SLACK_API_TOKEN'] != 'YOUR__SLACK__API_TOKEN_GOES_HERE')
            ), "If you want to post to slack then you need to add an api key to the config file!"
    assert ( not top_cat_config['POST_TO_FB_TF']
                or (top_cat_config['POST_TO_FB_TF'] and top_cat_config['FB_PAGE_ACCESS_TOKEN'] and top_cat_config['FB_PAGE_ACCESS_TOKEN'] != 'YOUR__FB__PAGE_ACCESS_TOKEN_GOES_HERE')
            ), "If you want to post to FB then you need to add a fb page_access_token to the config"
    return top_cat_config


def guarantee_tables_exist(db_conn):
    # Get a local cursor
    db_cur = db_conn.cursor()
    # Create the top_cat table and index
    for sql in """
            CREATE TABLE IF NOT EXISTS
                image (
                    image_id      INTEGER PRIMARY KEY,
                    timestamp_ins text not null default current_timestamp,
                    url           text not null,
                    file_hash     text not null,
                    title         text not null,
                    top_label     text not null
                );

            CREATE TABLE IF NOT EXISTS
                image_labels (
                    image_id      int not null,
                    label         text not null,
                    score         REAL,
                    FOREIGN KEY(image_id) REFERENCES image(image_id)
                );

            CREATE INDEX IF NOT EXISTS
                image_file_hash_index
                on  image (
                        file_hash
                    );

            CREATE INDEX IF NOT EXISTS
                image_url_index
                on  image (
                        url
                    );
            """.split(';'):
        db_cur.execute(sql.strip())
    db_conn.commit()


def get_thumb_content(img_content, image_max_size = (1000,1000)):
    pil_img = Image.open(StringIO.StringIO(img_content))
    pil_img.thumbnail(image_max_size, Image.ANTIALIAS)
    b = BytesIO()
    pil_img.save(b, format='jpeg')
    return b.getvalue()


def fix_imgur_url(url):
    """
    Sometimes people post imgur urls without the image or video extension.
    This grabs the extension and fixes the link so we go straight to the image or video:
    eg "http://i.imgur.com/mc316Un" -> "http://i.imgur.com/mc316Un.jpg"
    """
    if "imgur.com" in url:
        # Don't bother doing anything fancy if it already ends in .jpg
        if '.' not in url.split("/")[-1]:
            r = requests.get(url)
            # I could have used something fancier but this works fine
            img_link = re.findall('<link rel="image_src"\s*href="([^"]+)"/>', r.text)
            video_link = re.findall('<meta property="og:video"\s*content="([^"]+)"\s*/>', r.text)
            assert img_link or video_link, "imgur url fixing failed for " + url
            return (img_link or video_link)[0]
        else:
            # Just in case it ends in .gifv
            return url.replace('.gifv','.mp4')
    return url


def fix_giphy_url(url):
    if 'gfycat.com' in url:
        # keep just the caPiTALIZed key and return a nice predictable url
        return re.sub('.*gfycat.com/([^-]+)-.*', r'https://thumbs.gfycat.com/\1-mobile.mp4', url)
    return url

def fix_redd_url(url):
    return url+'/DASH_480.mp4' if 'v.redd.it' in url else url

def fix_url_in_dict(d):
    if d['gfycat']:
        return fix_giphy_url(d['gfycat'])
    else:
        return fix_redd_url(fix_imgur_url(d['url']))


def query_reddit_api(config, limit=10):
    # Try really hard to get reddit api results. Sometimes the reddit API gives back empty jsons.
    for attempt in range(config['MAX_REDDIT_API_ATTEMPTS']):
        r = requests.get(f"https://www.reddit.com/r/aww/top.json?limit={limit}", headers={'User-Agent': 'linux:top-cat:v0.2.0'})
        j = r.json()
        if j.get("data") is not None:
            print( "Succesfully queried the reddit api after", attempt+1, "attempts" , file=sys.stderr)
            break
        else:
            print( "Attempt", attempt, "at reddit api call failed. Trying again..." , file=sys.stderr)
        sleep(0.1)
    assert j.get("data") is not None, "Can't seem to query the reddit api! (Maybe try again later?)"
    # We've got the data for sure now.
    nice_jsons = pyjq.all('.data.children[].data|{title, url, orig_url: .url, gfycat: .media.oembed.thumbnail_url}', j)
    # fix imgur and giphy urls:
    nice_jsons = [ {**d, 'url':fix_url_in_dict(d)} for d in nice_jsons ]
    return nice_jsons

def add_image_content_to_post_d(post):
    " Add the image data to our post dictionary. Don't bother if it's already there. "
    if post.get('image') is None:
        post['image'] = requests.get(post['url'], stream=True).content
        post['image_hash'] = hashlib.sha1(post['image']).hexdigest()
    return post


def populate_labels_in_db_for_posts(reddit_response_json):
    # Make sure we have the images and labels stashed for any potentially new posts
    # Usually we just skip over a post since it's probably been in the top N for a few hours already
    for post_i, post in enumerate(reddit_response_json):
        db_cur.execute('SELECT image_id FROM image WHERE url=?', (post['url'],))
        image_found = db_cur.fetchone()
        if not image_found:
            # Did not find the url, must be a new post. Double check image table for existing hash
            add_image_content_to_post_d(post)
            db_cur.execute('SELECT image_id FROM image WHERE hash=?', (post['image_hash'],))
            image_reposted = db_cur.fetchone()
            if not image_reposted:
                # Ok, it's truly an original post, let's cache the labels
                #### FIXME: Add logic for caching labels


def repost_to_social_media(post, label):
    if top_cat_config['POST_TO_SLACK_TF']:
        slack_payload = {
            "token": top_cat_config['SLACK_API_TOKEN'],
            "channel": top_cat_config['SLACK_CHANNEL'],
            "text": "Top %s jpg on imgur (via /r/aww)" % (LABEL_TO_SEARCH_FOR),
            "username": "TopCat",
            "as_user": "TopCat",
            "attachments": json.dumps([
                    {
                        "fallback": "Top %s jpg on imgur (via /r/aww)" % (LABEL_TO_SEARCH_FOR),
                        "title": unicode(links_map_to_title[img]),
                        "image_url": img
                    }
                ])
        }
        requests.get('https://slack.com/api/chat.postMessage', params=slack_payload)

    if top_cat_config['POST_TO_FB_TF']:
        fb_api = facebook.GraphAPI(top_cat_config['FB_PAGE_ACCESS_TOKEN'])
        attachment =  {
            'name': 'top_cat',
            'link': img,
            'picture': img
        }
        status = fb_api.put_wall_post(message=unicode(links_map_to_title[img]), attachment=attachment)



def main():
    # FIXME: Fill in completely

    args = docopt(__doc__, version='0.2.0')

    # DONTFIXME: Don't use vision api
    # # Get google vision api credentials
    # credentials = GoogleCredentials.get_application_default()
    # service = discovery.build('vision', 'v1', credentials=credentials)

    top_cat_config = get_config()

    # Connect to the db. It creates the file if necessary.
    db_conn = sqlite3.connect(os.path.expanduser(top_cat_config['DB_FILE']))
    db_cur = db_conn.cursor()


    ### FIXME: Clean up and refactor into more functions

    # links = [ i["data"]["url"] for i in j["data"]["children"]]
    # fixed_links = [ unescape(fix_imgur_url(u)) for u in links ]
    # links_map_to_title = dict(zip(fixed_links, [ unicode(i["data"]["title"]) for i in j["data"]["children"]]))

    # def is_jpg(url):
    #     return requests.get(url, stream=True).headers.get('content-type') == 'image/jpeg'

    # #just_jpgs = filter(is_jpg, fixed_links)
    # just_jpgs = [l for l in fixed_links if is_jpg(l)]

    reddit_response_json = query_reddit_api(top_cat_config)

    populate_labels_in_db_for_posts(reddit_response_json)

    # We're ready to figure out if the post has climbed up the ranks and become a top post
    for label_to_search_for in top_cat_config['LABELS_TO_SEARCH_FOR']:
        # Iterate down the list of reddit posts and see if there's a label_to_search_for for the post.
        # FIXME: this part
        db_cur.execute("INSERT INTO image (url, file_hash, title, top_label) values (?,?,?,?)",
                    (img, file_hash, unicode(links_map_to_title[img]), top_label))
        db_conn.commit()
        db_cur.execute('SELECT image_id FROM image WHERE file_hash=?', (file_hash,))
        image_id = db_cur.fetchone()[0]
        # Print out each label and label's score. Also store each result in the db.)
        print( "Labels for " + img + ':' , file=sys.stderr)
        for label, score in labels_and_scores:
            print( '    ' + label + ' = ' + str(score) , file=sys.stderr)
            db_cur.execute("INSERT INTO image_labels (image_id, label, score) values (?,?,?)",
                        (image_id, label, score))
            db_conn.commit()

    ### FIXME: Old code
    for post in reddit_response_json:
        img_content = requests.get(img, stream=True).content
        # Make sure it's small enough for the vision api
        img_resized = get_thumb_content(img_content)
        image_content_b64 = base64.b64encode(img_resized)
        #Check if we already have the file in the db
        retrieved_from_db = False
        file_hash = hashlib.sha1(image_content_b64).hexdigest()
        db_cur.execute('SELECT top_label FROM image WHERE file_hash=?', (file_hash,))
        top_label = db_cur.fetchone()
        if top_label:
            #We've already got it.
            top_label = top_label[0]
            retrieved_from_db = True
            print("IMAGE ALREADY IN DB:", top_label, img, unicode(links_map_to_title[img]))


        if top_label == LABEL_TO_SEARCH_FOR:
            print("TOP %s FOUND!" % (LABEL_TO_SEARCH_FOR.upper()))
            print("Titled:", unicode(links_map_to_title[img]))
            print(img)
            if not retrieved_from_db :
                repost_to_social_media()
            # We found the top cat, no need to keep going through images
            break

    if top_label != LABEL_TO_SEARCH_FOR:
        # WHAT?!?!?!?! No cats???
        print("WARNING: The internet is broken. No top_cat found...")

    ### /FIXME: Old code

    ### /FIXME: Clean up and refactor into more functions




if __name__ == "__main__":
    # execute only if run as a script
    main()

