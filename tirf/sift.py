import math

import numpy as np
from scipy import misc
from scipy.ndimage import filters


def create_sift_features(img):
    """
    See: http://docs.opencv.org/trunk/da/df5/tutorial_py_sift_intro.html
    """
    harris_keypoints = filter_harris_points(compute_harris_score(img))
    dog_keypoints = difference_of_gaussian(img)
    contrast_keypoints = filter_low_contrast(img)

    print(img.shape)

    print('constrast', len(contrast_keypoints))
    print('harris', len(harris_keypoints))
    print('dog', len(dog_keypoints))
    keypoints = harris_keypoints & dog_keypoints & contrast_keypoints
    print(len(keypoints))


def compute_octaves(img, *, sigma=1.6, octave_nb=5):
    """
    Computes @octave_nb octaves with a @sigma starting from 1.6 and growing
    each time by a factor a sqrt(2).
    """
    octaves = []

    for _ in range(octave_nb):
        octaves.append(filters.gaussian_filter(img, sigma))
        sigma *= math.sqrt(2)

    return octaves


def scale_down(img):
    """
    Scales down the @img to half its original size.
    """
    return misc.imresize(img, .5)


def difference_of_gaussian(img):
    """
    Computes the Difference Of Gaussian:
        Several octaves are made, each a gaussian blur of the precedent with
        sigma starting from 1.6 and growing up by a factor of sqrt(2).
        Local extrema (max or min) are selected as potential keypoints between
        several layers of octaves.
    """
    octaves = compute_octaves(img)
    mid_octave = len(octaves) // 2
    keypoints = set() # Are made of tuples of coordinates (x, y)

    rows    = img.shape[0]
    columns = img.shape[1]
    for y in range(1, rows-1): # We are skipping the border pixels as they
        for x in range(1, columns-1): # probably won't be keypoints.
            min_extrema = float('inf')
            max_extrema = float('-inf')

            potential_keypoint = octaves[mid_octave].item(y, x, 0)

            for yy in range(-1, 2):
                for xx in range(-1, 2):
                    coord_y = y + yy
                    coord_x = x + xx
                    for octave in octaves:
                        min_extrema = min(min_extrema,
                                          octave.item(coord_y, coord_x, 0))
                        max_extrema = max(max_extrema,
                                          octave.item(coord_y, coord_x, 0))


            if potential_keypoint >= max_extrema or\
               potential_keypoint <= min_extrema:
                keypoints.add((x, y))

    return keypoints


def compute_harris_score(img, *, sigma=1.6):
    """
    Computes the harris score (from the harris corner detection algorithm)
    for each pixel.
    See for all the related notation:
        http://aishack.in/tutorials/harris-corner-detector
    """
    # First we are computing the derivating for each axis (x, and y) found
    # with the Taylor series.
    i_x = filters.gaussian_filter1d(img, sigma=sigma, order=1, axis=0)
    i_y = filters.gaussian_filter1d(img, sigma=sigma, order=1, axis=1)

    i_xx = filters.gaussian_filter(i_x * i_x, sigma)
    i_yy = filters.gaussian_filter(i_y * i_y, sigma)
    i_xy = filters.gaussian_filter(i_x * i_y, sigma)

    # We are now computing the score R for a window with the eigenvalues of
    # the matrix:
    #   M = [ Ix^2  IxIy ]
    #       [ IxIy  Iy^2 ]
    # With R = det M - trace(M)^2

    det_m = i_xx * i_yy - i_xy ** 2
    tr_m  = i_xx + i_yy

    return det_m - tr_m ** 2


def filter_harris_points(harris_scores, *, threshold=10):
    """
    Given a harris corner score for each pixel position, we are filtering
    all pixel' scores that are above the @threshold.
    """
    filtered_coords = set()

    rows    = harris_scores.shape[0]
    columns = harris_scores.shape[1]
    for y in range(1, rows-1):
        for x in range(1, columns-1):
            if harris_scores.item(y, x, 0) < threshold:
                filtered_coords.add((x, y))

    return filtered_coords


def filter_low_contrast(img, *, threshold=0.03):
    filtered_coords = set()

    rows    = img.shape[0]
    columns = img.shape[1]
    for y in range(1, rows-1):
        for x in range(1, columns-1):
            window = img[y-1:y+2, x-1:x+2, 0]

            std  = window.std()
            if std == 0:
                continue
            mean = window.mean()

            if abs((img.item(y, x, 0) - mean) / std) > threshold:
                filtered_coords.add((x, y))

    return filtered_coords
