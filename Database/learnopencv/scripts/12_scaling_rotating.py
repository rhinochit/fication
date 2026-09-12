'''
imagee sclaing and rotating 
'''
import cv2
import numpy as np

img = cv2.imread("images/1.jpg")     
img1 = cv2.resize(img,(500,500))

w,h = img1.shape[0], img1.shape[1]
m = cv2.getRotationMatrix2D((w/2,h/2),90,1) # build rotate function 
newimg = cv2.warpAffine(img1,m,(h,w))       # build new image using warpaffine 

cv2.imshow("frame",img1)
cv2.imshow("frame1",newimg)
cv2.waitKey(0)
cv2.destroyAllWindows()