'''
text over image
'''

import cv2

img= cv2.imread("images/2.jpg")

# img = cv2.resize(img, (1000,600))



txt = cv2.putText(img = img,
text = "hello world",
org = (360,80),
fontFace= cv2.FONT_HERSHEY_COMPLEX,
fontScale= 3,
color = (0, 255, 255),
lineType = cv2.LINE_8,
bottomLeftOrigin = False,
thickness = 3)

cv2.imshow("frame", img)
# print(img.shape)
cv2.waitKey(0)
cv2.destroyAllWindows()

'''
paramaters -> img, text, org, fontface, fontscale, color, thickness, linetype, bottomleftorigin,
org: (x,y)
fontFace: flag values search
color: BGR, (255,0,0)
lineType: flag values search
bottomLeftOrigin: optional; when true, origin is at bottom

'''

