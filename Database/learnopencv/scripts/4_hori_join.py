'''
horizontally join images
'''
import cv2
import numpy as np

v = np.array([1,2,3,1,2,3])
v1= np.hstack((v,v))

print(v1)