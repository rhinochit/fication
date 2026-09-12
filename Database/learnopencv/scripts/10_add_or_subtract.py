'''
add or subtract images
'''
import cv2
import numpy as np

img = cv2.imread("images/1.jpg")     
img1 = cv2.resize(img,(500,800))

img_ = cv2.imread("images/2.jpg")     
img2 = cv2.resize(img_,(500,800))

# new = cv2.addWeighted(img1,0.5,img2,0.5,1) #0.5 to each is the intensity 
new = cv2.subtract(img1,img2)

cv2.imshow("hello", new)
cv2.waitKey(0)
cv2.destroyAllWindows()

