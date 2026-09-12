'''
create blank images white and black
'''
import numpy as np
import cv2
img = cv2.imread("images/1.jpg")

new = np.ones((500,500,3), np.uint8)*255
new1 = np.zeros((500,500,3),np.uint8)*255

cv2.imshow("1",new)
cv2.imshow("2",new1)
cv2.waitKey(0)
cv2.destroyAllWindows()