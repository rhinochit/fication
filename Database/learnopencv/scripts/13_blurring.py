'''
blurring
'''
import cv2
import numpy as np

img = cv2.imread("images/1.jpg")     
img1 = cv2.resize(img,(500,500))   

g = cv2.GaussianBlur(img1, (9,9), 0)
h = cv2.medianBlur(img1, 5)
i = cv2.bilateralFilter(img1, 9,75,75)
pero = np.hstack((img1, g, h, i))

cv2.imshow("frame", pero)
cv2.waitKey(0)
cv2.destroyAllWindows()
 
'''
types of blurring:-
gaussian: result of blurring an image by gaussian funcition, graphics software, also used in aiml
median blurring: filter is non linear digitla filtering, widely used, preserves edges while removing noise (best algo for salt and pepper noise)
bilaterl noise: non linear, edge preserving, noise reducing, smoothening, weight based on gaussian distribution 

'''