from google.cloud import vision
from PIL import Image
from io import BytesIO, StringIO
from collections import Counter

def get_labels_for_im_using_vision_api(gvision_client, pil_img):
    # In case it's too big max it at one megapixel
    pil_img.thumbnail((1000,1000), Image.ANTIALIAS)
    b = BytesIO()
    pil_img.save(b, format='jpeg')
    im_bytes=b.getvalue()
    labels_for_im = gvision_client.label_detection({'content': im_bytes}, max_results=50)
    return ( [l.description.lower() for l in labels_for_im.label_annotations]
            ,[l.score for l in labels_for_im.label_annotations]
           )

def get_labels_from_frames_gvision(gvision_client, frames_in_video):
    # Counter can also keep track of fractional values
    proportion_label_in_post = Counter()
    for frame in frames_in_video:
        # resized_im, seg_map = model.run(frame)
        # unique_labels = np.unique(seg_map)
        # labels, num_pixels = np.unique(seg_map, return_counts=True)
        labels, scores = get_labels_for_im_using_vision_api(gvision_client, frame)
        normed_scores = [ s/len(frames_in_video) for s in scores]
        proportion_label_in_post += Counter(
                    dict(zip(labels, normed_scores))
                )
    return proportion_label_in_post



# # For debugging purposes

# pil_img = Image.open('/Users/nim/git/top_cat/imgs/sink_cats.jpg')
# l_s = get_labels_for_im_using_vision_api(pil_img)
# l_s

# frames = cast_to_pil_imgs(
#             extract_frames_from_im_or_video('/Users/nim/git/top_cat/imgs/ah4pflne11c51.mp4')
#         )


# vision_labels=get_labels_from_frames_gvision(frames)
# vision_labels
