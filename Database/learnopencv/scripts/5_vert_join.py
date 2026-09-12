'''
horizontally join images
'''
import cv2
import numpy as np

# v = np.array([1,2,3,1,2,3])
img = cv2.imread("images/2.jpg")     
 
img1 = cv2.resize(img,(500,500))
# h = np.hstack((img1,img1))
v = np.vstack((img1,img1))
h = np.hstack((v,v))
cv2.imshow("hello", h)

cv2.waitKey(0)          
cv2.destroyAllWindows()  
# v1= np.hstack((v,v))
