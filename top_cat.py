#!/usr/bin/env python
import requests
import re
import base64
from googleapiclient import discovery
from oauth2client.client import GoogleCredentials
import sys
import json
import sqlite3
import hashlib

conn = sqlite3.connect('top_cat.db')
cur = conn.cursor()
# Create the top_cat table and index
map(lambda s: cur.execute(s),
    ["""
        CREATE TABLE IF NOT EXISTS
            image (
                timestamp_ins text not null default current_timestamp,
                url           text not null,
                file_hash     text not null,
                title         text not null,
                top_label     text not null
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




SLACK_API_TOKEN = "xoxp-116638699686-115285855585-115287802689-6f8293f619125c15b2430d164208ac1c"

def fix_imgur_url(url):
    if "imgur" in url:
        if '.' not in url.split("/")[-1]:
            r = requests.get(url)
            img_link = re.findall('<link rel="image_src"\s*href="([^"]+)"/>', r.text)
            if img_link:
                return img_link[0]
            else:
                return "Failure"
    return url

credentials = GoogleCredentials.get_application_default()
service = discovery.build('vision', 'v1', credentials=credentials)

# Try really hard to get the data. Sometimes the reddit API gives back empty jsons.
for attempt in range(20):
    r = requests.get("https://www.reddit.com/r/aww/top.json")
    j = r.json()
    if j.get("data") is not None:
        print >> sys.stderr, "Succesfully queried the reddit api after", attempt+1, "attempts"
        break
    else:
        print >> sys.stderr, "Attempt", attempt, "at reddit api call failed. Trying again..."
assert j.get("data") is not None, "Can't seem to query the reddit api! (Maybe try again later?)"


links = [ i["data"]["url"] for i in j["data"]["children"]]
fixed_links = [ fix_imgur_url(u) for u in links ]
links_map_to_title = dict(zip(fixed_links, [ i["data"]["title"] for i in j["data"]["children"]]))

just_imgur_jpgs = [l for l in fixed_links if "imgur" in l and ".jpg" in l]

for img in just_imgur_jpgs:
    img_response = requests.get(img, stream=True)
    image_content = base64.b64encode(img_response.content)
    #Check if we already have the file in the db
    file_hash = hashlib.sha1(image_content).hexdigest()
    cur.execute('SELECT top_label FROM image WHERE file_hash=?', (file_hash,))
    label = cur.fetchone()
    if label:
        #We already got it.
        print "IMAGE ALREADY IN DB:", img, links_map_to_title[img]
    else:
        # Annotate image with google image api
        service_request = service.images().annotate(body={
            'requests': [{
                'image': {
                    'content': image_content.decode('UTF-8')
                },
                'features': [{
                    'type': 'LABEL_DETECTION',
                    'maxResults': 5
                }]
            }]
        })
        response = service_request.execute()
        print >> sys.stderr, response
        label = response['responses'][0]['labelAnnotations'][0]['description']
        print >> sys.stderr, 'Found label: %s for %s' % (label, img)

        # Add it to the db:
        cur.execute("INSERT INTO image (url, file_hash, title, top_label) values (?,?,?,?)",
                    (img, file_hash, links_map_to_title[img], label))
        conn.commit()

    if label == "cat":
        print img, links_map_to_title[img]
        slack_payload = {
            "token": SLACK_API_TOKEN,
            "channel": "#top_cat",
            "text": "Top cat jpg on imgur (via /r/aww)",
            "username": "TopCat",
            "as_user": "TopCat",
            "attachments": json.dumps([
                    {
                        "fallback": "Top cat jpg on imgur (via /r/aww)",
                        "title": links_map_to_title[img],
                        "image_url": img
                    }
                ])
        }
        requests.get('https://slack.com/api/chat.postMessage', params=slack_payload)

        # We found the top cat, no need to keep going through images
        break
