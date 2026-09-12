'''
draw line, rect, circle, ellipse over image
'''

import cv2

img= cv2.imread("images/2.jpg")
img = cv2.resize(img, (500,600))

# newimg = cv2.line(img = img,pt1 = (150,300), pt2= (350,300), color= (0,255,255), thickness=4, lineType= 4)
# newimg = cv2.rectangle(img = img, pt1 = (150,100), pt2 = (350, 300), color= (0,255,255), thickness=4, lineType= 4)
# newimg = cv2.circle(img = img, center = (200,200),radius=100, color= (0,255,255), thickness=4, lineType= 4)
newimg = cv2.ellipse(img = img, center = (200,200),axes= (50,100),angle=30,startAngle=0, endAngle=360, color= (0,255,255), thickness=4, lineType= 4)


cv2.imshow("frame", img)
cv2.waitKey(0)
cv2.destroyAllWindows()

'''
Linetype: search karlo
pt1: starting point of line
pt2: end point of line

in rect pt1 and pt2 are corner end points 
for circle: if thickeness = -1, it fills in teh circle with same color

'''

