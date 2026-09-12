'''
morphological operations 
types:
erosion
dilation
opening
closing
morpholigical gradient
black hat
top hat
'''

import cv2
import numpy as np
img = cv2.imread("images/1.jpg")
img = cv2.resize(img,(300,300))

m = np.ones((10,10),np.int8)
er = cv2.erode(img, m, iterations=1)
di = cv2.dilate(img,m,iterations=1)
op = cv2.morphologyEx(img,cv2.MORPH_OPEN,m,iterations=1)
cl = cv2.morphologyEx(img,cv2.MORPH_CLOSE,m,iterations=1)
bh = cv2.morphologyEx(img,cv2.MORPH_BLACKHAT,m,iterations=1)
wh = cv2.morphologyEx(img,cv2.MORPH_TOPHAT,m,iterations=1)
h = np.hstack((er,di,op))
h1 = np.hstack((cl,bh,wh))
v = np.vstack((h,h1))

cv2.imshow("1",v)
cv2.waitKey(0)
cv2.destroyAllWindows()