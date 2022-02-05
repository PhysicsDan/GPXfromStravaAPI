# GPXfromStravaAPI
Create GPX files from datastreams downloaded using the Strava API
Currently the limitations are the GPX file will only contain latitude, longitude, time and elevation, not HR.

DISCLAIMER: I am a hobbiest so this may not be the 'best' way to do the following but it has worked well for me.

The StravaAPI doesn't allow for direct downloading of GPX files. Therefore individual latitude, longitude and elevation values are downloaded and then converted into a gpx file using the `gpxpy.gpx` module.

Requirements: see requirements.txt

Usage:
```
python main.py
```

You can also use:
```
python main.py --dir /path/to/directory
```
if the python file and folders etc are in a different directory

You can also specify the location of where you want to store your data and api keys relative to the working directory
```
python main.py --keys path/to/api/keys --data path/to/data/folder
```
