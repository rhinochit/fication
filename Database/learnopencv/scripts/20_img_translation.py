'''
image translation such as cropping shifting and animating
'''


import cv2
import numpy as np

img = cv2.imread("images/1.jpg")
img = cv2.resize(img,(500,500))
m = np.float32([[10,10,100],[10,11,50]])
new = cv2.warpAffine(img,m,(500,500))

cv2.imshow("1",img)
cv2.imshow("2",m)
cv2.imshow("3",new)
cv2.waitKey(0)
cv2.destroyAllWindows()