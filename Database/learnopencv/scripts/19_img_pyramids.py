'''
image pyramids: to lower or raise resolution, or resize
divide or multiply size by 2
'''

import cv2
import numpy as np
img = cv2.imread("images/1.jpg")
print(img.shape)

smallimg = cv2.pyrDown(img)
print(smallimg.shape)
bigimg = cv2.pyrUp(img)
print(bigimg.shape)