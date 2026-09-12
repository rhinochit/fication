import cv2

img = cv2.imread("images/2.jpg", -1)  # image read
img = cv2.resize(img, (500,500))
cv2.imshow("frame", img)    # shows the image in frame, (keep spacing between comma abd img)
# cv2.imshow("frame1", img)
cv2.waitKey(1000)          # wait for 1000 miliseconds or 1 second (if passed 0 instead if 1000, ends on pressinf any ey)
cv2.destroyAllWindows()     # closes all frames or windows
#cv2.destroyWindow           # destroys only that one window
print(img.shape)

'''
cv2.imread_color specifies to load color image, transparency ignored , flag default = 1
cv2.imread_grayscale specifies to load an image in grayscale mode, flag = 0
cv2.imread_unchanged specifies to load an image, flag = -1
img = cv2.imread("images/2.jpg", FLAG)
'''
