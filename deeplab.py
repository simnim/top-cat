# https://github.com/tensorflow/models/blob/master/research/deeplab/deeplab_demo.ipynb
# Mostly taken from ^ but cleaned and modified a bit to be easier for me to use.

import os
from io import BytesIO
import tarfile
import tempfile
from six.moves import urllib

from matplotlib import gridspec
from matplotlib import pyplot as plt
import numpy as np
from PIL import Image
from collections import Counter

import tensorflow as tf
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'
tf.compat.v1.logging.set_verbosity(tf.compat.v1.logging.ERROR)

class DeepLabModel(object):
    """Class to load deeplab model and run inference."""

    INPUT_TENSOR_NAME = 'ImageTensor:0'
    OUTPUT_TENSOR_NAME = 'SemanticPredictions:0'
    INPUT_SIZE = 513
    FROZEN_GRAPH_NAME = 'frozen_inference_graph'
    LABEL_NAMES = np.asarray([
        'background',    #0
        'aeroplane',     #1
        'bicycle',       #2
        'bird',          #3
        'boat',          #4
        'bottle',        #5
        'bus',           #6
        'car',           #7
        'cat',           #8
        'chair',         #9
        'cow',           #10
        'diningtable',   #11
        'dog',           #12
        'horse',         #13
        'motorbike',     #14
        'person',        #15
        'pottedplant',   #16
        'sheep',         #17
        'sofa',          #18
        'train',         #19
        'tv',            #20
    ])


    def __init__(self, tarball_path):
        """Creates and loads pretrained deeplab model."""
        self.graph = tf.Graph()

        graph_def = None
        # Extract frozen graph from tar archive.
        tar_file = tarfile.open(tarball_path)
        for tar_info in tar_file.getmembers():
            if self.FROZEN_GRAPH_NAME in os.path.basename(tar_info.name):
                file_handle = tar_file.extractfile(tar_info)
                graph_def = tf.compat.v1.GraphDef.FromString(file_handle.read())
                break

        tar_file.close()

        if graph_def is None:
            raise RuntimeError('Cannot find inference graph in tar archive.')

        with self.graph.as_default():
            tf.import_graph_def(graph_def, name='')

        self.sess = tf.compat.v1.Session(graph=self.graph)

    def run(self, image):
        """Runs inference on a single image.

        Args:
          image: A PIL.Image object, raw input image.

        Returns:
          resized_image: RGB image resized from original input image.
          seg_map: Segmentation map of `resized_image`.
        """
        width, height = image.size
        resize_ratio = 1.0 * self.INPUT_SIZE / max(width, height)
        target_size = (int(resize_ratio * width), int(resize_ratio * height))
        resized_image = image.convert('RGB').resize(target_size, Image.ANTIALIAS)
        batch_seg_map = self.sess.run(
            self.OUTPUT_TENSOR_NAME,
            feed_dict={self.INPUT_TENSOR_NAME: [np.asarray(resized_image)]})
        seg_map = batch_seg_map[0]
        return resized_image, seg_map



def get_labels_from_frames_deeplab(model, frames_in_video):
    # Counter can also keep track of fractional values
    proportion_label_in_post = Counter()
    for frame in frames_in_video:
        resized_im, seg_map = model.run(frame)
        unique_labels = np.unique(seg_map)
        labels, num_pixels = np.unique(seg_map, return_counts=True)
        labels_text = [ model.LABEL_NAMES[l] for l in labels ]
        proportion_label_in_post += Counter(
                        dict(zip(labels_text, 1.0*num_pixels/seg_map.size/len(frames_in_video)))
                    )
    return proportion_label_in_post
