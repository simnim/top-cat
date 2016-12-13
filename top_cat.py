#!/usr/local/bin/env python
import requests
import re
import base64
from googleapiclient import discovery
from oauth2client.client import GoogleCredentials


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
    # [END construct_request]
    # [START parse_response]
    response = service_request.execute()
    print response
    label = response['responses'][0]['labelAnnotations'][0]['description']
    print('Found label: %s for %s' % (label, img))
    if label = "cat":
        break
    # [END parse_response]
