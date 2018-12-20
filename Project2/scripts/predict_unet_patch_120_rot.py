#!/usr/bin/env python3

# API
import src.load as load
import src.patch as patch
import src.submission as submission
import src.transformation as transformation

# Model
from models.definitions.unet_120 import get_unet_120

import matplotlib.image as mpimg
import numpy as np
import tensorflow as tf
import matplotlib.pyplot as plt
import scipy.misc as sp
import os,sys
from PIL import Image
import keras
from keras.models import *
from keras.layers import Input
from keras.regularizers import *
from keras.optimizers import Adam
import re
from shutil import copyfile
import math

def f1_custom(labels, preds):
    true_positives = np.sum(labels*preds)
    try:
        precision = true_positives / np.sum(preds)
        recall = true_positives / np.sum(labels)
        f1 = 2 * precision * recall / (precision + recall)
    except ZeroDivisionError:
        return 0.0
    return f1


# Name of output file (in ../models/output/) where the model's weight will be stored
OUTPUT_NAME = 'UNET_patch_120_rot'

# Size of patches to split images
PATCH_SIZE = 120

# Overlapping pixels between patches
OVERLAP = 100

# Number of classes on which to build the models
NUM_CLASSES = 1

# Pixel dimensions for training images
IMG_NUM_DIM = 3 

# Fix RNG for reproducibility
np.random.seed(1)

# ================== LOAD ORIGINAL TRAINING DATA ==================
print("Loading test set...")

# Load images
test_imgs = load.load_test_set()

# Make patches out of the testset images
test_patches, overlap_image, nPatches = patch.make_patch_and_flatten(test_imgs, PATCH_SIZE, OVERLAP)

# ================== LOAD VALIDATION SET ==================
print("Loading validation set...")

# Load validation set (used to determine the best threshold to discriminate foreground from backgound)
val_patches , val_gt_patches, _, _ = load.load_training_data_and_patch(load.PROVIDED_DATA_DIR , patch_size=PATCH_SIZE, 
                                random_selection=False, proportion=1.0, overlap=OVERLAP)
val_gt_patches = np.expand_dims(val_gt_patches,axis=3)

# Make sure that groundtruths are filled with only 0's and 1's
val_gt_patches = (val_gt_patches > 0.5).astype(int)

# ================== LOAD MODEL ==================
print("Loading model " + OUTPUT_NAME)

input_img = Input((PATCH_SIZE, PATCH_SIZE, IMG_NUM_DIM), name='img')
model = get_unet_120(input_img, NUM_CLASSES, n_filters=16, dropout=0.4, batchnorm=True)
model.load_weights(submission.MODELS_OUTPUT_DIR + OUTPUT_NAME + '.h5')

# ================== MAKE PREDICTIONS ==================
print("Making predictions on test patches...")
predictions_test = model.predict(test_patches,verbose=1)
print("Making predictions on validation patches...")
predictions_val = model.predict(val_patches,verbose=1)

# Reconstruct test predictions
predictions = patch.reconstruct_from_flatten(np.squeeze(predictions_test), overlap_image, nPatches, OVERLAP)

# ================== FIND BEST THRESHOLD  ==================
print("Looking for best threshold...")
THRESHOLD_INC = 0.05
threshold = np.arange(0, 1, THRESHOLD_INC)
best_score = 0
best_thr = 0

for thr in threshold:
    # Compute predictions on validation set and compute F1 score
    predictions_val_bin = (predictions_val > thr).astype(int)
    score = f1_custom(val_gt_patches,predictions_val_bin)

    if score > best_score: # We got our best score yet, save threshold
        best_thr = thr
        best_score = score

print("Best threshold is " + str(best_thr))

# ================== GENERATE SUBMISSION FILE ==================
print("Creating submission file " + OUTPUT_NAME)
predictions_bin = (predictions > best_thr).astype(int)

THRESHOLD_FOREGROUND = 0.25
submission.predictions_to_submission(predictions_bin, OUTPUT_NAME + ".csv", THRESHOLD_FOREGROUND)
