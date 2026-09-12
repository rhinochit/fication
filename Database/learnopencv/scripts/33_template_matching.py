'''
template matching of an image within another image
'''
import cv2
import numpy as np

img = cv2.imread("images/2.jpg")
img = cv2.cvtColor(img,cv2.COLOR_BGR2GRAY)

temp = cv2.imread("images/6.jpg")
temp = cv2.cvtColor(temp,cv2.COLOR_BGR2GRAY)

w,h = temp.shape[1],temp.shape[0]
res = cv2.matchTemplate(img,temp,cv2.TM_CCORR_NORMED)
thre = 0.95
l = np.where(res>=thre)

for i in zip(*l[::-1]):
    cv2.rectangle(img,i,(i[0]+h,i[1]+w), (0,0,255),2)

cv2.resize(img,(500,600))
cv2.imshow("0",res)
# cv2.imshow("1",img)
# cv2.imshow("2",temp)
cv2.waitKey(0)
cv2.destroyAllWindows()