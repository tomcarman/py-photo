# py-photo
A python script to organise photos.

## Usage

### Step 1. Run py-photo

`python py-photo.py`

This will generate a .csv with old path name, and new path name (based on exif data)

### Step 2. Run py-filemover

`python py-filemover.py`

This will move files from the old path name, to the new path name - using the .csv generated in step 1.
