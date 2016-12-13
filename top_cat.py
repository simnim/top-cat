#!/usr/bin/env python
import requests
import re
import base64
from googleapiclient import discovery
from oauth2client.client import GoogleCredentials
import sys

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

        #FIXME: Make a function that posts to slack. Here's an example string to post:
        # https://slack.com/api/chat.postMessage?token=xoxp-116638699686-115285855585-115287802689-6f8293f619125c15b2430d164208ac1c&channel=%23top_cat&text=Top%20cat%20on%20imgur&attachments=%5B%20%20%20%20%20%20%20%20%20%7B%20%20%20%20%20%20%20%20%20%20%20%20%20%22fallback%22%3A%20%22cat%20picture%22%2C%20%20%20%20%20%20%20%20%20%20%20%20%20%22color%22%3A%20%22%2336a64f%22%2C%20%20%20%20%20%20%20%20%20%20%20%20%20%22title%22%3A%20%22Cats%20to%20the%20max%22%2C%20%20%20%20%20%20%20%20%20%20%20%20%20%22image_url%22%3A%20%22http%3A%2F%2Fi.imgur.com%2FLAJvT7p.jpg%22%20%20%20%20%20%20%20%20%20%7D%20%20%20%20%20%5D&pretty=1

        break
