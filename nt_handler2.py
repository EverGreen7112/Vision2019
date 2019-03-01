from datetime import datetime

from networktables import NetworkTables
from reflectivev import GripPipeline
import cv2
from threading import Thread
from subprocess import call
import logging

im = None
capturing = True
success = False


def update_image():
    global im
    global success #tosefet
    global capturing
    nt = NetworkTables.getTable("ImageProcessing")
    last_id = cam_id = int(nt.getNumber("currentCamera", defaultValue=0))
    cam = cv2.VideoCapture(-1) #(cam_id)
    #print (cam)
    try:
        while capturing:
            #cam_id = int(nt.getNumber("currentCamera", defaultValue=1))
            if last_id != cam_id:
                cam.release()
                cam = cv2.VideoCapture(-1)
            last_id = cam_id
            success, im = cam.read()
            
    finally:
        cam.release()
        print ("Thread's done!")


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    print ("Starting")
    #call("v4l2-ctl --device=/dev/video0 -c exposure_auto=1 -c exposure_absolute=5", shell=True)
    #call("v4l2-ctl --device=/dev/video1 -c exposure_auto=1 -c exposure_absolute=5", shell=True)
    NetworkTables.initialize("10.71.12.2") # The ip of the roboRIO
    t = Thread(target=update_image)
    t.start()
    pipeline = GripPipeline()
    networkTableImageProcessing = NetworkTables.getTable("ImageProcessing")
    contour_count = 2
    try:
        while (success == False) or not NetworkTables.isConnected():
            pass
            print ("NT connection: %r" % NetworkTables.isConnected())
        [networkTableImageProcessing.delete(s) for s in networkTableImageProcessing.getKeys()]
        while True:
            print ("Processing...")
            pipeline.process(im)
            contours = sorted(pipeline.filter_contours_output, key=cv2.contourArea, reverse=True)
            contour_count = max(contour_count, len(contours))
            print ("contours: ", len(contours))
            i = 0
            
            for i, c in enumerate(contours):
                
                
                networkTableImageProcessing.putNumber('contourArea%d' % i, cv2.contourArea(c))
                print ('contourArea%d'% i, cv2.contourArea(c))
                x, y, w, h = cv2.boundingRect(c)

                networkTableImageProcessing.putNumber('contourNum%d'% i, len(contours))
                networkTableImageProcessing.putNumber('width%d' % i, w)
                # print ('width%d' % i, w)
                networkTableImageProcessing.putNumber('height%d' % i, h)  # CR: typo lol
                # print 'height%d' % i, h
                networkTableImageProcessing.putNumber('x%d' % i, x)
                # print 'x%d' % i, x
                networkTableImageProcessing.putNumber('y%d' % i, y)
                # print 'y%d' % i, y
                networkTableImageProcessing.putBoolean('isUpdated%d' % i, True)
                
                
                print ("isUpdated%d" % i, True)
                print (w)
                print (h)
                print (x)
                print (y)
                if (i > 0):
                    break     
            for i in range(len(contours), contour_count):
                networkTableImageProcessing.putBoolean('isUpdated%d' % i, False)
    finally:
        capturing = False
        print ("Done!")
