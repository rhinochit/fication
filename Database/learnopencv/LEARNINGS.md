# What I learned

A walk through the `scripts/` folder, grouped by topic. Script numbers in
brackets.

## Images: read, show, save

- **Reading** [`1`, `0`]: `cv2.imread(path, flag)` returns a NumPy array in
  **BGR** order (not RGB). Flags: `1` / `IMREAD_COLOR` (default, drops alpha),
  `0` / `IMREAD_GRAYSCALE`, `-1` / `IMREAD_UNCHANGED` (keeps alpha). Returns
  `None` on failure instead of raising — always check for it.
- **Showing** [`1`]: `cv2.imshow(window, img)` then `cv2.waitKey(ms)` to pump the
  GUI event loop. `waitKey(0)` waits forever; any positive value waits that many
  milliseconds. `cv2.destroyAllWindows()` (or `destroyWindow(name)`) cleans up.
- **Path handling** [`0`]: building the path from
  `os.path.dirname(os.path.abspath(__file__))` makes a script runnable from any
  working directory. The other scripts assume the repo root as CWD.
- **`img.shape`** [`1`, `19`]: `(height, width, channels)` — height first.
- **Saving** [`14`]: `cv2.imwrite(filename, img)`; the extension picks the
  encoder.

## Resizing and joining

- **Resize** [`2`]: `cv2.resize(img, (width, height))` — the size tuple is
  `(w, h)`, the opposite order to `shape`.
- **Stacking** [`4`, `5`, `18`]: `np.hstack` / `np.vstack` tile images into a
  grid for side-by-side comparison. All pieces must share dimensions and channel
  count.
- **Iterate a folder** [`6`]: `os.listdir("images")` + `cv2.imread` to loop over
  every image.

## Colour

- **BGR arrays** [`3`]: printing the array shows rows of `[B, G, R]` triples,
  0–255 `uint8`.
- **`cv2.cvtColor`** [`24`, `30`, `31`, `33`]: convert colour spaces, e.g.
  `cv2.COLOR_BGR2GRAY`. Grayscale is the required input for thresholding,
  contours, template matching, most detectors.
- **Blank canvases** [`26`]: `np.ones((h, w, 3), np.uint8) * 255` is white,
  `np.zeros((h, w, 3), np.uint8)` is black. Assign `img[:] = [b, g, r]` to flood
  fill.

## Drawing and text

- **Text** [`7`]: `cv2.putText(img, text, org, fontFace, fontScale, color,
  thickness, lineType)`. `org` is the `(x, y)` of the text's bottom-left corner.
- **Shapes** [`8`]: `cv2.line`, `cv2.rectangle` (two opposite corners),
  `cv2.circle`, `cv2.ellipse`. `thickness=-1` fills the shape.
- **Polygons** [`9`]: `cv2.polylines(img, [pts], isClosed, color, thickness)`;
  `pts` is a list of `np.array` point arrays.

## Arithmetic

- **Blend / add / subtract** [`10`]: `cv2.addWeighted(a, wa, b, wb, gamma)`
  cross-fades two same-size images; `cv2.subtract` / `cv2.add` do saturating
  per-pixel math (clamped to 0–255, unlike raw NumPy which wraps).

## Filtering and edges

- **Blur** [`13`]: `GaussianBlur` (general smoothing), `medianBlur` (best for
  salt-and-pepper noise, keeps edges), `bilateralFilter` (edge-preserving
  smoothing, slower).
- **Canny** [`11`]: `cv2.Canny(img, threshold1, threshold2)` for edge maps.
- **Morphology** [`18`]: on a structuring element (`np.ones((k, k))`):
  `erode`, `dilate`, and via `morphologyEx` — `MORPH_OPEN` (erode→dilate, removes
  specks), `MORPH_CLOSE` (dilate→erode, fills holes), `MORPH_GRADIENT`,
  `MORPH_TOPHAT`, `MORPH_BLACKHAT`.
- **Pyramids** [`19`]: `cv2.pyrDown` / `pyrUp` halve / double resolution.

## Geometric transforms

- **Rotation** [`12`]: `cv2.getRotationMatrix2D(center, angle, scale)` → 2×3
  matrix → `cv2.warpAffine(img, M, (w, h))`.
- **Translation** [`20`]: a `np.float32([[1, 0, tx], [0, 1, ty]])` matrix through
  `warpAffine` shifts the image.
- **Affine vs perspective** [`21`]: affine keeps parallel lines parallel — needs
  3 point correspondences (`getAffineTransform` + `warpAffine`). Perspective
  keeps straight lines straight — needs 4 correspondences, no 3 collinear
  (`getPerspectiveTransform` + `warpPerspective`).
- **Crop** [`25`]: plain NumPy slicing `img[y1:y2, x1:x2]`.

## Video

- **Playback** [`15`]: `cap = cv2.VideoCapture(path)`, loop while
  `cap.isOpened()`, `ret, frame = cap.read()`, break when `ret` is `False`.
  Always `cap.release()`.
- **Webcam** [`16`]: same API with device index `0`.
- **Frame rate** [`15`, `17`]: the `waitKey(n)` delay inside the loop controls
  playback speed — small `n` = fast, large `n` = slow motion.
- **Key handling**: `cv2.waitKey(n) & 0xFF == ord("p")` is the portable way to
  test a key press.
- **Writing video** [`29`]: `cv2.VideoWriter_fourcc(*"mp4v")` picks the codec,
  `cv2.VideoWriter(name, fourcc, fps, (w, h))` opens the file, `out.write(frame)`
  per frame. Frame size must match or nothing is written. `cv2.flip(frame, 1)`
  mirrors.
- **Background subtraction** [`22`]: `cv2.createBackgroundSubtractorMOG2()`, then
  `fgmask = sub.apply(frame)` isolates moving foreground.
- **Extract frames** [`23`]: read in a loop and `cv2.imwrite` each frame.

## Trackbars / interactive windows

- [`27`, `28`]: `cv2.namedWindow(name)` + `cv2.createTrackbar(label, window, min,
  max, callback)`; read the live value with `cv2.getTrackbarPos`. Built an
  RGB colour picker with three trackbars driving `img[:] = [b, g, r]`.

## Thresholding and segmentation

- [`30`]: `cv2.threshold(gray, thresh, maxval, type)` binarises an image.
  `THRESH_BINARY` uses the value you pass; `THRESH_OTSU` picks the threshold
  automatically from the histogram; adaptive thresholding varies it per region.
  Thresholding is the usual first step to separate foreground from background.

## Contours

- **Find and draw** [`31`]: threshold → `cv2.findContours(thresh, mode, method)`
  returns `(contours, hierarchy)`. `RETR_TREE` keeps the full nesting;
  `CHAIN_APPROX_SIMPLE` compresses straight runs to endpoints.
  `cv2.drawContours(img, contours, -1, color, thickness)` draws them all.
- **Moments / centroid** [`32`]: `M = cv2.moments(cnt)`, centroid is
  `(M["m10"]/M["m00"], M["m01"]/M["m00"])` — mark it with a filled circle.
  (Related: convex hull, contour area/perimeter.)

## Template matching

- [`33`]: `cv2.matchTemplate(image, template, method)` slides the template and
  returns a score map. `np.where(res >= threshold)` gives match locations;
  draw a rectangle of the template's size at each. Both inputs grayscale.

## Still open

- `34_face_detection.py` — Haar cascade / DNN face detection, not done yet.

## Recurring gotchas

- BGR, not RGB.
- `shape` is `(h, w, c)` but `resize` takes `(w, h)`.
- `imread` returns `None` on a bad path instead of raising.
- On Windows, prefer forward slashes or raw strings for paths; several early
  scripts hard-code a `C://Users//...` path that only works on my machine.
- Forgetting `waitKey` means the window never actually paints.
