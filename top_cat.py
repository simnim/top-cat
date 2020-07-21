#!/usr/bin/env python

"""
Nick Hahner 2017
Ever wanted to automate finding the top cute cat picture from /r/aww to send to your friends?
All you need to do is run ./top_cat.py and your life will change forever.

You'll need to create ~/.top_cat.json if you want to find dogs instead!
You can also add your slack api key to ^ if you want a nifty slack integration.
All items in the config file are optional.
"""

import requests
import re
import base64
from googleapiclient import discovery
from oauth2client.client import GoogleCredentials
import facebook
import sys
import json
import toml
import sqlite3
import hashlib
import os
from time import sleep
import StringIO
from PIL import Image
from io import BytesIO

# Because the reddit api links use escaped html strings ie &amp;
from xml.sax.saxutils import unescape


# Start off with default config and override with our config
this_script_dir = os.path.dirname(os.path.realpath(__file__))
default_config = toml.load(this_script_dir+'/top_cat_deault.toml')

CONFIG_FILE_LOC = os.path.expanduser("~/.top_cat.toml")
# Let's query the config file
if os.path.isfile(CONFIG_FILE_LOC):
    try:
        top_cat_user_config = toml.load(CONFIG_FILE_LOC)
    except Exception as e:
        print >> sys.stderr, "Malformed config file at '%s'" % (CONFIG_FILE_LOC)
        exit(1)
else:
    top_cat_user_config = dict()

top_cat_config = {**default_config, **top_cat_user_config}

# If we plan on posting to social media, let's make sure we have tokens to try
assert ( not POST_TO_SLACK_TF
            or (POST_TO_SLACK_TF and SLACK_API_TOKEN and SLACK_API_TOKEN != 'YOUR__SLACK__API_TOKEN_GOES_HERE')
        ), "If you want to post to slack then you need to add an api key to the config file!"
assert ( not POST_TO_FB_TF
            or (POST_TO_FB_TF and FB_PAGE_ACCESS_TOKEN and FB_PAGE_ACCESS_TOKEN != 'YOUR__FB__PAGE_ACCESS_TOKEN_GOES_HERE')
        ), "If you want to post to FB then you need to add a fb page_access_token to the config"


# Get google vision api credentials
credentials = GoogleCredentials.get_application_default()
service = discovery.build('vision', 'v1', credentials=credentials)

# Connect to the db. It creates the file if necessary.
conn = sqlite3.connect(os.path.expanduser("~/.top_cat.db"))
cur = conn.cursor()
# Create the top_cat table and index
map(lambda s: cur.execute(s),
    [   """
        CREATE TABLE IF NOT EXISTS
            image (
                image_id      INTEGER PRIMARY KEY,
                timestamp_ins text not null default current_timestamp,
                url           text not null,
                file_hash     text not null,
                title         text not null,
                top_label     text not null
            );
        """
    ,
        """
        CREATE TABLE IF NOT EXISTS
            image_labels (
                image_id      int not null,
                label         text not null,
                score         REAL,
                FOREIGN KEY(image_id) REFERENCES image(image_id)
            );
        """
    ,
        """
        CREATE INDEX IF NOT EXISTS
            image_file_hash_index
            on  image (
                    file_hash
                );
        """
    ])


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
    if "imgur" in url:
        if '.' not in url.split("/")[-1]:
            r = requests.get(url)
            # I could have used bs4, but it'd actually be more verbose in this case.
            img_link = re.findall('<link rel="image_src"\s*href="([^"]+)"/>', r.text)
            video_link = re.findall('<meta property="og:video"\s*content="([^"]+)"\s*/>', r.text)
            assert img_link or video_link, "imgur url fixing failed for " + url
            return (img_link or video_link)[0]
    return url

# Try really hard to get reddit api results. Sometimes the reddit API gives back empty jsons.
for attempt in range(MAX_REDDIT_API_ATTEMPTS):
    r = requests.get("https://www.reddit.com/r/aww/top.json")
    j = r.json()
    if j.get("data") is not None:
        print >> sys.stderr, "Succesfully queried the reddit api after", attempt+1, "attempts"
        break
    else:
        print >> sys.stderr, "Attempt", attempt, "at reddit api call failed. Trying again..."
    sleep(0.1)
assert j.get("data") is not None, "Can't seem to query the reddit api! (Maybe try again later?)"


links = [ i["data"]["url"] for i in j["data"]["children"]]
fixed_links = [ unescape(fix_imgur_url(u)) for u in links ]
links_map_to_title = dict(zip(fixed_links, [ unicode(i["data"]["title"]) for i in j["data"]["children"]]))

def is_jpg(url):
    return requests.get(url, stream=True).headers.get('content-type') == 'image/jpeg'

#just_jpgs = filter(is_jpg, fixed_links)
just_jpgs = [l for l in fixed_links if is_jpg(l)]

for img in just_jpgs:
    img_content = requests.get(img, stream=True).content
    img_resized = get_thumb_content(img_content)
    # Make sure it's small enough for the vision api
    image_content_b64 = base64.b64encode(img_resized)
    #Check if we already have the file in the db
    retrieved_from_db = False
    file_hash = hashlib.sha1(image_content_b64).hexdigest()
    cur.execute('SELECT top_label FROM image WHERE file_hash=?', (file_hash,))
    top_label = cur.fetchone()
    if top_label:
        #We've already got it.
        top_label = top_label[0]
        retrieved_from_db = True
        print "IMAGE ALREADY IN DB:", top_label, img, unicode(links_map_to_title[img])
    else:
        # Annotate image with google image api
        service_request = service.images().annotate(body={
            'requests': [{
                'image': {
                    'content': image_content_b64.decode('UTF-8')
                },
                'features': [{
                    'type': 'LABEL_DETECTION',
                    'maxResults': 10
                }]
            }]
        })
        response = service_request.execute()
        assert  response.get('responses') and \
                len(response['responses']) > 0 and\
                response['responses'][0].get('labelAnnotations') \
            , \
                "Google vision api didn't seem to like the image... it returned no results. Wat do?"
        labels_and_scores = [ (annot['description'], annot['score']) for annot in response['responses'][0]['labelAnnotations'] ]
        top_label = labels_and_scores[0][0]
        # Add the image to the db:
        cur.execute("INSERT INTO image (url, file_hash, title, top_label) values (?,?,?,?)",
                    (img, file_hash, unicode(links_map_to_title[img]), top_label))
        conn.commit()
        # Now get back the image_id of what we just inserted...
        cur.execute('SELECT image_id FROM image WHERE file_hash=?', (file_hash,))
        image_id = cur.fetchone()[0]

        # Print out each label and label's score. Also store each result in the db.
        print >> sys.stderr, "Labels for " + img + ':'
        for label, score in labels_and_scores:
            print >> sys.stderr, '    ' + label + ' = ' + str(score)
            cur.execute("INSERT INTO image_labels (image_id, label, score) values (?,?,?)",
                        (image_id, label, score))
            conn.commit()


    if top_label == LABEL_TO_SEARCH_FOR:
        print "TOP %s FOUND!" % (LABEL_TO_SEARCH_FOR.upper())
        print "Titled:", unicode(links_map_to_title[img])
        print img
        if not retrieved_from_db :
            if POST_TO_SLACK_TF:
                slack_payload = {
                    "token": SLACK_API_TOKEN,
                    "channel": SLACK_CHANNEL,
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

            if POST_TO_FB_TF:
                fb_api = facebook.GraphAPI(top_cat_config['FB_PAGE_ACCESS_TOKEN'])
                attachment =  {
                    'name': 'top_cat',
                    'link': img,
                    'picture': img
                }
                status = fb_api.put_wall_post(message=unicode(links_map_to_title[img]), attachment=attachment)

        # We found the top cat, no need to keep going through images
        break

if top_label != LABEL_TO_SEARCH_FOR:
    # WHAT?!?!?!?! No cats???
    print "WARNING: The internet is broken. No top_cat found..."
