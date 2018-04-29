import glob
import numpy as np
import scipy.misc

'''Almost entirely ripped off from https://github.com/AshishBora/csgm'''

def center_crop(x, crop_h, crop_w=None, resize_w=64):
    if crop_w is None:
        crop_w = crop_h
    h, w = x.shape[:2]
    j = int(round((h - crop_h)/2.))
    i = int(round((w - crop_w)/2.))
    return scipy.misc.imresize(x[j:j+crop_h, i:i+crop_w],
                               [resize_w, resize_w])

def transform(image, npx=64, is_crop=True, resize_w=64):
    # npx : # of pixels width/height of image
    if is_crop:
        cropped_image = center_crop(image, npx, resize_w=resize_w)
    else:
        cropped_image = image
    return np.array(cropped_image)/127.5 - 1.
    # im = np.array(cropped_image)
    # return (im - np.mean(im))/np.std(im)
    # return cropped_image

def merge(images, size):
    h, w = images.shape[1], images.shape[2]
    img = np.zeros((h * size[0], w * size[1], 3))
    for idx, image in enumerate(images):
        i = idx % size[1]
        j = idx // size[1]
        img[j*h:j*h+h, i*w:i*w+w, :] = image
    return img

def inverse_transform(images):
    return (images+1.)/2.

def imsave(images, size, path):
    return scipy.misc.imsave(path, merge(images, size))

def save_images(images, size, image_path):
    return imsave(inverse_transform(images), size, image_path)

def imread(path, is_grayscale=False):
    if is_grayscale:
        return scipy.misc.imread(path, flatten=True).astype(np.float)
    else:
        return scipy.misc.imread(path).astype(np.float)

def get_image(image_path, image_size, is_crop=True, resize_w=64, is_grayscale=False):
    return transform(imread(image_path, is_grayscale), image_size, is_crop, resize_w)

def get_full_input(path='data/celeba/img_align_celeba/', max_index=None):
    """Create input tensors"""
    image_paths = glob.glob(path + '*')
    image_paths.sort()
    image_paths = image_paths
    image_size = 108
    if max_index: image_paths = image_paths[:max_index]
    return np.array([get_image(image_path, image_size).reshape([64*64*3]) for image_path in image_paths])
