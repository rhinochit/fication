'''
countouring around image
'''
import cv2
img = cv2.imread("images/1.jpg")
img = cv2.pyrDown(img)
img1 = cv2.cvtColor(img,cv2.COLOR_BGR2GRAY)
r,thre = cv2.threshold(img1, 100, 255, cv2.THRESH_BINARY)
c,h = cv2.findContours(thre,cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
new = cv2.drawContours(img,c,-1,(255,0,0),2)
cv2.imshow("1",img)
cv2.imshow("2",thre)
cv2.waitKey(0)
cv2.destroyAllWindows()
