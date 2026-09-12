# learnopencv

My notebook of OpenCV (`cv2`) practice scripts, worked through one concept at a
time. Each file in [`scripts/`](scripts/) is a small, self-contained experiment,
numbered in the order I learned it.

See [`LEARNINGS.md`](LEARNINGS.md) for a written summary of what each script
taught me.

## Setup

```bash
python -m venv venv
venv\Scripts\activate        # Windows
pip install opencv-python numpy
```

## Running a script

Scripts use relative paths like `images/2.jpg`, so run them from the project
root:

```bash
python scripts/1_read.py
```

Most windows wait on a key press; a few loop until you press `p`.

## Notes

- `venv/` and large media (`*.mp4`, a couple of big JPEGs) are gitignored. The
  small sample images under `images/` are kept so most scripts run as-is.
- `0_check.py` builds its image path from the script location, so it works from
  any working directory — the pattern I should have used everywhere.
