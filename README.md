# GPXfromStravaAPI
Create GPX files from datastreams downloaded using the Strava API
The StravaAPI doesn't allow for direct downloading of GPX files. Therefore individual latitude, longitude and elevation values are downloaded and then converted into a gpx file using the `gpxpy.gpx` module.

Currently the limitations are the GPX file will only contain latitude, longitude, time and elevation, not heartrate although that is easy enough to add but was not required by me.

DISCLAIMER: I am a hobbiest so this may not be the 'best' way to do the following but it has worked well for me.

## Setting up the API
There is a handy guide [here](https://medium.com/swlh/using-python-to-connect-to-stravas-api-and-analyse-your-activities-dummies-guide-5f49727aac86) that shows you how to set up an Strava so you can make API requests. The main information you need is:
- User Code (Shown in the API section of Strava settings)
- Secret Code (Shown in the API section of Strava settings)
- Authentication Token (see the linked guide on how to get this)

You need to add this info to the `client_info.json file` in the `keys` folder. After that when you run the code for the first time it should generate the relavent tokens etc that are required.

Requirements: see requirements.txt

## Usage:
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
