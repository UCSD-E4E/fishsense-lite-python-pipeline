import numpy as np
import cv2 as cv

#resize the image for convenient verification of the processed image by the user.
def imageResize(img, resize_val):
    scale_percent = resize_val # percent of original size
    width = int(img.shape[1] * (scale_percent / 100))
    height = int(img.shape[0] * (scale_percent / 100))
    dim = (width, height)   

    img = cv.resize(img, dim, interpolation = cv.INTER_AREA)
    return img

#linearize the raw sensor date
def linearization(img):
    img[img > 65000] = img.min()

    # b,g,r = cv.split(img)
    # b = ((b - b.min()) * (1/(b.max() - b.min()) * 65535)).astype('uint16')
    # g = ((g - g.min()) * (1/(g.max() - g.min()) * 65535)).astype('uint16')
    # r = ((r - r.min()) * (1/(r.max() - r.min()) * 65535)).astype('uint16')
    # return np.dstack((b,g,r))
    img = ((img - img.min()) * (1/(img.max() - img.min()) * 65535)).astype(np.uint16)
    return img

#apply a demosaicing algorithm to create a 3 color channel RGB image 
def demosaic(img):
    img = cv.demosaicing(img, cv.COLOR_BayerGB2BGR) 
    return img

#denoise the image by convolving the data with a low-pass filter
def denoising(img, val):
    img = cv.blur(img, (val,val))
    return img

#provides the possibility to convert the image to greyscale
def colorSpace(img, colour):
    if not colour:
        img = cv.cvtColor(img, cv.COLOR_BGR2GRAY)
    return img

#apply exposure compensation to the image, and handle any clipping that might be ocurring
def exposureComp(img, val):
    img = img * val
    img = img.astype(np.uint16)
    _, img = cv.threshold(img, 65535, 65535, cv.THRESH_TRUNC)
    return img

#provides the ability to adjust the low, mid and high tones separately
def toneCurve(img, params):
    low = params[0]
    mid = params[1]
    high = params[2]

    img[img <= 21845] *= np.asarray(low).astype(np.uint16)
    img[(21845 < img) & (img < 43690)] *= np.asarray(mid).astype(np.uint16)
    img[img >= 43690] *= np.asarray(high).astype(np.uint16)

     #img.astype(np.uint16)
    _, img = cv.threshold(img, 65535, 65535, cv.THRESH_TRUNC)
    return img

#maps the channel value to new values according to the gamma function
def gammaCorrection (img, gamma):
    img_buf = (img)/65535
    buf = np.power(img_buf, gamma) * 65535
    buf = buf.astype(np.uint16)
    return buf

#provides white balance adjustments to the image based on the grey world algorithm
def greyWorldWB(img, colour):
    if colour == True: 
        b, g, r = cv.split(img)
        r_avg = cv.mean(r)[0]
        g_avg = cv.mean(g)[0]
        b_avg = cv.mean(b)[0]

        kr = g_avg / r_avg
        kg = 1
        kb = g_avg / b_avg  

        r = cv.addWeighted(src1=r, alpha=kr, src2=0, beta=0, gamma=0)
        g = cv.addWeighted(src1=g, alpha=kg, src2=0, beta=0, gamma=0)
        b = cv.addWeighted(src1=b, alpha=kb, src2=0, beta=0, gamma=0)

        balance_img = cv.merge([b, g, r])

    else:
        balance_img = img   
    return balance_img

def hist_eq(img: np.ndarray) -> (np.ndarray, np.ndarray, np.ndarray):
    """
    This function will do histogram equalization on a given 1D np.array
    meaning will balance the colors in the image.
    For more details:
    https://en.wikipedia.org/wiki/Histogram_equalization
    **Original function was taken from open.cv**
    :param img: a 1D np.array that represent the image
    :return: imgnew -> image after equalization, hist-> original histogram, histnew -> new histogram
    """

    # Flattning the image and converting it into a histogram
    histOrig, bins = np.histogram(img.flatten(), 65536, [0, 65535])
    # Calculating the cumsum of the histogram
    cdf = histOrig.cumsum()
    # Places where cdf = 0 is ignored and the rest is stored
    # in cdf_m
    cdf_m = np.ma.masked_equal(cdf, 0)
    # Normalizing the cdf
    cdf_m = (cdf_m - cdf_m.min()) * 65535 / (cdf_m.max() - cdf_m.min())
    # Filling it back with zeros
    cdf = np.ma.filled(cdf_m, 0)


    # Creating the new image based on the new cdf
    imgEq = cdf[img.astype('uint16')]
    histEq, bins2 = np.histogram(imgEq.flatten(), 65536, [0, 65536])

    return imgEq, histOrig, histEq

def hsitogramEqualize(imgOrig: np.ndarray) -> (np.ndarray, np.ndarray, np.ndarray):
    """
        Equalizes the histogram of an image
        The function will fist check if the image is RGB or gray scale
        If the image is gray scale will equalizes
        If RGB will first convert to YIQ then equalizes the Y level
        :param imgOrig: Original Histogram
        :return: imgnew -> image after equalization, hist-> original histogram, histnew -> new histogram
    """

    if len(imgOrig.shape) == 2:

        img = imgOrig * 65536
        imgEq, histOrig, histEq = hist_eq(img)

    else:
        img = imgOrig
        # img = cv.cvtColor(imgOrig, cv.COLOR_BGR2HSV)
        img[:, :, 0], histOrig, histEq = hist_eq(img[:, :, 0])
        img[:, :, 1], histOrig, histEq = hist_eq(img[:, :, 1])
        img[:, :, 2], histOrig, histEq = hist_eq(img[:, :, 2])
        # imgEq = cv.cvtColor(img, cv.COLOR_HSV2BGR)
        imgEq = img

    return imgEq, histOrig, histEq

def equalizeHist(img):
    img, _, _ = hsitogramEqualize(img)

    return img