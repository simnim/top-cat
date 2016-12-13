#!/usr/bin/env python
import requests
import re
import base64
from googleapiclient import discovery
from oauth2client.client import GoogleCredentials
import sys
import json

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

r = requests.get("https://www.reddit.com/r/aww/top.json")
j = r.json()

links = [ i["data"]["url"] for i in j["data"]["children"]]
fixed_links = [ fix_imgur_url(u) for u in links ]
links_map_to_title = dict(zip(fixed_links, [ i["data"]["title"] for i in j["data"]["children"]]))

just_imgur_jpgs = [l for l in fixed_links if "imgur" in l and ".jpg" in l]

for img in just_imgur_jpgs:
    img_response = requests.get(img, stream=True)
    image_content = base64.b64encode(img_response.content)
    service_request = service.images().annotate(body={
        'requests': [{
            'image': {
                'content': image_content.decode('UTF-8')
            },
            'features': [{
                'type': 'LABEL_DETECTION',
                'maxResults': 1
            }]
        }]
    })
    response = service_request.execute()
    print >> sys.stderr, response
    label = response['responses'][0]['labelAnnotations'][0]['description']
    print >> sys.stderr, 'Found label: %s for %s' % (label, img)
    if label == "cat":
        print img, links_map_to_title[img]
        slack_payload = {
            "token": SLACK_API_TOKEN,
            "channel": "#top_cat",
            "text": "Top cat jpg on imgur (via /r/aww)",
            "attachments": json.dumps([
                    {
                        "fallback": "Top cat jpg on imgur (via /r/aww)",
                        "title": links_map_to_title[img],
                        "image_url": img
                    }
                ])
        }
        requests.get('https://slack.com/api/chat.postMessage', params=slack_payload)
        break
