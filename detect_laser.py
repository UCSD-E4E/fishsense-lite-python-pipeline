from pathlib import Path
import cv2
import os
import sys
import numpy as np
import rawpy
import json

from camera_imaging_pipeline.src.image_processing import imageProcessing

from detect_laser_line import return_line, get_vanishing_point_2d

def get_vanishing_point(laser_path: Path, calibration_path: Path):

    return get_vanishing_point_2d(laser_path, calibration_path)

def get_masked_image_matrix(laser_path: Path, 
                         calibration_path:Path, img: np.ndarray):
    
    # Make sure that the file is a JPG
    if type(img) != np.ndarray:
        sys.exit(1)

    if len(np.shape(img)) == 3:
        print('3')
        # Get the line
        img_clone = img.copy()
        start_point, end_point = return_line(laser_path, calibration_path)
        cv2.line(img, start_point, end_point, color=(0,0,255), thickness=75) 

        # Create the mask and the masked image
        mask = cv2.inRange(img_clone, (0,0,255), (0,0,256))/255
        mask_rgb = np.dstack((mask,mask,mask)).astype(np.uint8)
        masked_image = img * mask_rgb

        return masked_image

    elif (len(np.shape(img)) == 2):
        print(np.max(img))
        img_clone = img.copy()
        start_point, end_point = return_line(laser_path, calibration_path)
        cv2.line(img_clone, start_point, end_point, color=0, thickness=75)

        mask = cv2.inRange(img_clone, 0, 1)/255
        mask = mask.astype(np.uint8)
        masked_image = img * mask

        return masked_image
    sys.exit(1)

def get_masked_image_rgb(laser_path: Path, 
                         calibration_path:Path, filepath: Path):
    
    # Make sure that the file is a JPG
    if filepath.suffix != ".JPG":
        sys.exit(1)
    
    img = cv2.imread(filepath.as_posix())
    img_clone = img.copy()

    # Get the line
    start_point, end_point = return_line(laser_path, calibration_path)
    cv2.line(img_clone, start_point, end_point, color=(0,0,255), thickness=75) 

    # Create the mask and the masked image
    mask = cv2.inRange(img_clone, (0,0,255), (0,0,256))/255
    mask_rgb = np.dstack((mask,mask,mask)).astype(np.uint8)
    masked_image = img * mask_rgb

    return masked_image

def get_masked_image_raw(laser_path: Path, 
                         calibration_path:Path, filepath: Path):
    
    # Make sure that the file is a JPG
    if filepath.suffix != ".ORF":
        sys.exit(1)
    
    with rawpy.imread(filepath.as_posix()) as raw:

        raw_img = raw.raw_image.copy()
        
        img = (raw_img/np.amax(raw_img)*255).astype(np.uint8)
        
        img_clone = cv2.cvtColor(img, cv2.COLOR_GRAY2RGB)

        # Get the line
        start_point, end_point = return_line(laser_path, calibration_path)
        cv2.line(img_clone, start_point, end_point, color=(0,0,255), thickness=75) 

        # Create the mask and the masked image
        mask = (cv2.inRange(img_clone, (0,0,255), (0,0,256))/255).astype(np.uint8)
        masked_image = img * mask

        return masked_image
    
def detect_laser_raw(masked_raw: np.ndarray):

    contour_mask = cv2.inRange(masked_raw, 255, 256)
    
    kernel = np.ones((5,5), np.uint8)
    contour_mask = cv2.morphologyEx(contour_mask, cv2.MORPH_CLOSE, kernel)
    contours, _ = cv2.findContours(contour_mask, 
                                           cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

    return contours

def display_masked_image(laser_path: Path, 
                         calibration_path:Path, filepath: Path, raw: bool, param_path=None):
    
    if not raw:
        masked_image = get_masked_image_rgb(laser_path, calibration_path, filepath)
        cv2.namedWindow("Masked_Window", cv2.WINDOW_NORMAL)
        cv2.imshow("Masked_Window",masked_image)
        cv2.waitKey(0)
        cv2.destroyAllWindows()

    else:
        masked_image = get_masked_image_raw(laser_path, calibration_path, filepath)

        contours = detect_laser_raw(masked_image)

        # masked_rgb = cv2.demosaicing(masked_image, cv2.COLOR_BAYER_GB2BGR)
        params = json.load(open(params_path))
        processor = imageProcessing()
        masked_rgb, _ = processor.applyToImage(masked_image, params)

        for cnt in contours:
            cv2.drawContours(masked_rgb,[cnt],0,(0,0,65535),thickness=10)
        cv2.namedWindow("Masked_Window", cv2.WINDOW_NORMAL)
        cv2.imshow("Masked_Window",masked_rgb)
        # resized = cv2.resize(masked_rgb, (1800, 1350))
        cv2.imshow("resized", masked_rgb[1000:2000, 1000:3000])
        
        cv2.waitKey(0)
        cv2.destroyAllWindows()
        
def display_detection(laser_path: Path, 
                         calibration_path:Path, filepath: Path, params_path: Path):


        masked_image = get_masked_image_raw(laser_path, calibration_path, filepath)

        contours = detect_laser_raw(masked_image)   

        params = json.load(open(params_path))
        processor = imageProcessing()
        processed_image, _ = processor.applyToImage(filepath.as_posix(), params)
        
        # processed_image = processed_image.astype(np.uint8)
        for cnt in contours:
            cv2.drawContours(processed_image,[cnt],0,(0,0,65535),thickness=-1)
        
        resized = cv2.resize(processed_image, (1800, 1350))
        cv2.imshow("resized", resized)
        # cv2.namedWindow("Masked_Window", cv2.WINDOW_NORMAL)
        # cv2.imshow("Masked_Window",masked_rgb)
        
        # cv2.imshow("cropped", processed_image[1000:2000, 1000:3000])
        
        cv2.waitKey(0)
        cv2.destroyAllWindows()

    
laser_path = Path("C:/Users/Hamish/Documents/E4E/Fishsense/fishsense-lite-python-pipeline/files/laser-calibration-output-7-13.dat")
calibration_path = Path("C:/Users/Hamish/Documents/E4E/Fishsense/fishsense-lite-python-pipeline/files/fsl-01d-lens.dat")
data_path = Path("C:/Users/Hamish/Documents/E4E/Fishsense/fishsense-lite-python-pipeline/data/7_23_nathans_pool/FSL-01D Fred")

for file in os.listdir(data_path.as_posix()):

    filepath = data_path.joinpath(file)
    if filepath.suffix != ".ORF":
        continue
    
    params_path = Path('C:/Users/Hamish/Documents/E4E/Fishsense/fishsense-lite-python-pipeline/camera_imaging_pipeline/params1.json')

    print(f"Processing {file}")
    # display_detection(laser_path, calibration_path, filepath, params_path)
    display_masked_image(laser_path, calibration_path, filepath, True, params_path)