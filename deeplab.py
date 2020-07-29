import os
from io import BytesIO
import tarfile
import tempfile
from six.moves import urllib

from matplotlib import gridspec
from matplotlib import pyplot as plt
import numpy as np
from PIL import Image

#%tensorflow_version 1.x
import tensorflow as tf

# https://github.com/tensorflow/models/blob/master/research/deeplab/deeplab_demo.ipynb
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



deeplabv3_model_tar = tf.keras.utils.get_file(
	fname=config['DEEPLABV3_FILE_NAME'],
	origin="http://download.tensorflow.org/models/"+config['DEEPLABV3_FILE_NAME'],
	cache_subdir='models')

MODEL = DeepLabModel(deeplabv3_model_tar)


def look_for_desired_labels(img_or_video, labels_to_keep):
  original_im = Image.open(img_file)
  print('running deeplab on image %s...' % img_file)
  resized_im, seg_map = MODEL.run(original_im)
  unique_labels = np.unique(seg_map)


