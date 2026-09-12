'''
thresholding image: most common segmentation technique, allows to separate foreground from background of image
thresholding is binarization of image

3 ways:
simple thresholding
otsu's thresholding
adaptive thresholding
'''
import cv2
import numpy as np

img = cv2.imread("images/2.jpg")
img = cv2.resize(img, (600,400))
img = cv2.cvtColor(img,cv2.COLOR_BGR2GRAY)
_,threshold = cv2.threshold(img,50,100,cv2.THRESH_OTSU)

cv2.imshow("1", img)
cv2.imshow("2", threshold)
cv2.waitKey(0)
cv2.destroyAllWindows()
'''
in thresholding an arbitrary value is chosen as a threshold, OTSU'S METHOD avoid having to choose the value
determining it automatically
'''