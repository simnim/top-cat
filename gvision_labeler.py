# from google.cloud import vision
import os
from collections import Counter
from io import BytesIO

from PIL import Image

# Average of the score for a label across all frames > 50%
SCORE_CUTOFF = 0.5


def get_labels_for_im_using_vision_api(gvision_client, pil_img):
    # In case it's too big max it at one megapixel
    pil_img.thumbnail((1000, 1000), Image.ANTIALIAS)
    b = BytesIO()
    pil_img.save(b, format="png")
    im_bytes = b.getvalue()
    labels_for_im = gvision_client.label_detection(
        {"content": im_bytes}, max_results=50
    )
    return (
        [label.description.lower() for label in labels_for_im.label_annotations],
        [label.score for label in labels_for_im.label_annotations],
    )


# NOTE: I'm averaging the score accross all the sampled frames. Could use more tinkering.
def get_labels_from_frames_gvision(gvision_client, frames_in_video):
    # Counter can also keep track of fractional values
    proportion_label_in_post = Counter()
    for frame in frames_in_video:
        labels, scores = get_labels_for_im_using_vision_api(gvision_client, frame)
        # After dividing by the number of frames
        normed_scores = [s / len(frames_in_video) for s in scores]
        # we can add fractional scores to the total for each label
        proportion_label_in_post += Counter(dict(zip(labels, normed_scores)))
    # Delete labels below threshold
    for label in list(proportion_label_in_post.keys()):
        if proportion_label_in_post[label] < SCORE_CUTOFF:
            # print(f'deleting {label} from consideration {proportion_label_in_post[label]} < {SCORE_CUTOFF}', file=sys.stderr)
            del proportion_label_in_post[label]
    return proportion_label_in_post


## For when we import
def get_labelling_func_given_config(config):
    # If the google creds env var is not set, try to get it from the user config
    if (
        not os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")
        and config["GOOGLE_APPLICATION_CREDENTIALS"] != "PATH_TO_YOUR_CONFIG_JSON"
    ):
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = config[
            "GOOGLE_APPLICATION_CREDENTIALS"
        ]
    from google.cloud import vision

    gvision_client = vision.ImageAnnotatorClient()

    def labelling_funtion_gvision(frames):
        return get_labels_from_frames_gvision(gvision_client, frames)

    return labelling_funtion_gvision


# # For debugging purposes

# pil_img = Image.open('/Users/nim/git/top_cat/imgs/sink_cats.jpg')
# gvision_client = vision.ImageAnnotatorClient()
# pil_img.thumbnail((1000,1000), Image.ANTIALIAS)
# b = BytesIO()
# pil_img.save(b, format='jpeg')
# im_bytes=b.getvalue()
# labels_for_im = gvision_client.label_detection({'content': im_bytes}, max_results=50)


# pil_img = Image.open('/Users/nim/git/top_cat/imgs/sink_cats.jpg')
# l_s = get_labels_for_im_using_vision_api(pil_img)
# l_s

# frames = cast_to_pil_imgs(
#             extract_frames_from_im_or_video('/Users/nim/git/top_cat/imgs/ah4pflne11c51.mp4')
#         )


# vision_labels=get_labels_from_frames_gvision(frames)
# vision_labels
