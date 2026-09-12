'''
countouring around image
'''
import cv2
img = cv2.imread("images/5.jpg")
img = cv2.pyrDown(img)
img1 = cv2.cvtColor(img,cv2.COLOR_BGR2GRAY)
r,thre = cv2.threshold(img1, 225, 250, cv2.THRESH_BINARY)
c,h = cv2.findContours(thre,cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
new = cv2.drawContours(img,c,-1,(255,0,0),2)
for cnt in c:
    m = cv2.moments(cnt)
    x = int(m["m10"]/m["m00"])
    y = int(m["m01"]/m["m00"])
    cv2.drawContours(img,c,-1,(0,0,255),4)
    cv2.circle(img,(x,y),2,(255,0,0),-1)

cv2.imshow("1",img)
cv2.imshow("2",thre)
cv2.waitKey(0)
cv2.destroyAllWindows()