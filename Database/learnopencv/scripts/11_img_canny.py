'''
edges program
'''
import cv2
import numpy as np

img = cv2.imread("images/1.jpg")     
img1 = cv2.resize(img,(500,800))

new = cv2.Canny(img1,100,100) # canny for lines and edges
cv2.imshow("frame",new)
cv2.waitKey(0)
cv2.destroyAllWindows()