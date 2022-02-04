import requests
import pandas as pd
import json
from time import time, sleep
from os import mkdir, listdir, path, getcwd, chdir
import gpxpy.gpx
from datetime import datetime, timedelta
from argparse import ArgumentParser


class StravaApiHelper:
	def __init__(self, args=None):
		print(f'Current directory: {getcwd()}')
		if args == None:
			self.keys_folder = 'keys/'
			self.data_folder = 'data/'
		else:
			if args.keys[-1] == '\\' or args.data[-1] == '\\':
				raise ValueError(
					'Please use unix style folder separation. i.e. path/to/file')
			chdir(args.dir)
			self.keys_folder = args.keys if args.keys[-1] == '/' else args.keys + '/'
			self.data_folder = args.data if args.data[-1] == '/' else args.data + '/'
		self.exceed_counter = 0
		print(f'Data printed to: {self.data_folder}')
		print(f'API tokens stored in: {self.keys_folder}')
		for f in [self.keys_folder, self.data_folder, self.data_folder + 'figs']:
			if not path.isdir(f):
				mkdir(f)
				print(f'Made folder: {f}')

	def GetInitialStravaTokens(self):
		#Source: medium
		with open(self.keys_folder + 'client_info.json') as f:
			init_info = json.load(f)
		response = requests.post(
			url='https://www.strava.com/oauth/token',
			data=init_info
		)  # Save json response as a variable
		strava_tokens = response.json()
		with open(self.keys_folder + 'strava_tokens.json', 'w') as outfile:
			json.dump(strava_tokens, outfile)
		with open(self.keys_folder + 'strava_tokens.json') as check:
			data = json.load(check)
		print('The following was written to strava_tokens.json:\n', data)
		if 'errors' in [*data]:
			raise ValueError(
				'Unable to retrieve API tokens place an updated code in client_info.json')

	def GetUpdatedStravaTokens(self):
		if 'strava_tokens.json' not in listdir(self.keys_folder):
			self.GetInitialStravaTokens()
		with open(self.keys_folder + 'strava_tokens.json') as json_file:
			# If access_token has expired then
			strava_tokens = json.load(json_file)

		# use the refresh_token to get the new access_token
		# Make Strava auth API call with current refresh token
		if strava_tokens['expires_at'] < time():

			with open(self.keys_folder + 'client_info.json') as f:
				init_info = json.load(f)
			client_id = init_info['client_id']
			client_secret = init_info['client_secret']

			response = requests.post(
				url='https://www.strava.com/oauth/token',
				data={
					'client_id': client_id,
					'client_secret': client_secret,
					'grant_type': 'refresh_token',
					'refresh_token': strava_tokens['refresh_token']
				}
			)  # Save response as json in new variable
			new_strava_tokens = response.json()  # Save new tokens to file
			with open(self.keys_folder + 'strava_tokens.json', 'w') as outfile:
				# Use new Strava tokens from now
				json.dump(new_strava_tokens, outfile)
			# Open the new JSON file and print the file contents
			strava_tokens = new_strava_tokens

	def GetInitialData(self):
		"""
		This function is unused but is handy if you want to see all
		available fields that could be included in activity summary.
		"""
		with open(self.keys_folder + 'strava_tokens.json') as json_file:
			strava_tokens = json.load(json_file)  # Loop through all activities
		url = "https://www.strava.com/api/v3/activities"
		# Get first page of activities from Strava with all fields
		access_token = strava_tokens['access_token']
		r = requests.get(url + '?access_token=' + access_token)
		r = r.json()
		df = pd.json_normalize(r)
		df.to_csv('strava_activities_all_fields.csv')

	def GetActivitySummary(self, recent=True):
		print('Getting activity summary...')
		cols = ('id', 'name', 'manual', 'distance', 'moving_time',
                'total_elevation_gain',	'type', 'start_date_local',
                'average_speed', 'average_cadence', 'weighted_average_watts',
                'average_heartrate', 'max_heartrate', 'start_latlng')

		# Get the tokens from file to connect to Strava
		with open(self.keys_folder + 'strava_tokens.json') as json_file:
			strava_tokens = json.load(json_file)  # Loop through all activities
		page = 1
		url = "https://www.strava.com/api/v3/activities"
		# Create the dataframe ready for the API call to store your activity data
		access_token = strava_tokens['access_token']
		if 'activity_summary_raw.csv' in listdir(self.data_folder):
			activities = pd.read_csv(
				self.data_folder + 'activity_summary_raw.csv')
		else:
			activities = pd.DataFrame(columns=cols)
		new_activities = pd.DataFrame(columns=cols)
		flag = True
		while flag:
			# get page of activities from Strava
			r = requests.get(url + '?access_token=' + access_token +
							 '&per_page=200' + '&page=' + str(page))
			r = r.json()

			if isinstance(r, dict):
				check = r['message']
				if check == 'Rate Limit Exceeded':
					print('Rate Limit Exceeded, sleeping for 15 mins')
					self.exceed_counter += 1
					if self.exceed_counter >= 10:
						exit('Over number of daily API requests\nRestart tomorrow')
					sleep(20)
					for i in range(15):
						print(f'Sleep remaining:{int(15-i)} minutes')
						sleep(60)
					r = requests.get(
						url + '?access_token=' + access_token + '&per_page=200' + '&page=' + str(page))
					r = r.json()

			# if no results then exit loop
			if not r:  # if nothing to return
				break
			# otherwise add new data to dataframe
			for x in range(len(r)):
				if int(r[x]['id']) in activities['id'].to_list():
					flag = False
					break
				for col in cols:
					value = r[x][col] if col in r[x].keys() else 0
					new_activities.loc[x + (page - 1) * 200, col] = value
			page += 1  # Export your activities file as a csv
		# to the folder you're running this script in
		new_activities = new_activities.append(activities, ignore_index=True)
		new_activities.to_csv(
			self.data_folder + 'activity_summary_raw.csv', index=False)
		print('Activity summary updated!')

	def GetGPXFile(self, supress=True):
		print('Downloading GPX files...')
		if 'gpx' not in listdir(self.data_folder):
			mkdir(self.data_folder + '/gpx')
		with open(self.keys_folder + 'strava_tokens.json') as json_file:
			strava_tokens = json.load(json_file)
		access_token = strava_tokens['access_token']
		header = {'Authorization': 'Bearer ' + access_token}
		param = {'keys': ['latlng']}

		id_list = pd.read_csv(self.data_folder + 'activity_summary_raw.csv',
							  usecols=['id', 'start_date_local', 'type', 'manual', 'start_latlng'])
		for idx in id_list.index:
			id = id_list.loc[idx, 'id']
			if id_list.loc[idx, 'manual']:
				if not supress:
					print(f'Skipping manual activity: {id}')
				continue
			# act_type = id_list.loc[idx,'type']
			# if act_type not in ['Run', 'Walk', 'Hike', 'Ride']:
			#     if not supress:
			#         print(f'Skipping activity type: {act_type}')
			#     continue
			if len(id_list.loc[idx, 'start_latlng'].split(',')) != 2:
				if not supress:
					print(f'Skipping activity, no GPS: {id}')
				continue

			start_time = id_list.loc[idx, 'start_date_local']

			if f'{id}.gpx' in listdir(f'{self.data_folder}/gpx/'):
				continue  # skip activities that are alre

			url = f"https://www.strava.com/api/v3/activities/{id}/streams"
			latlong = requests.get(url, headers=header, params={
								   'keys': ['latlng']}).json()
			time_list = requests.get(url, headers=header, params={
									 'keys': ['time']}).json()
			altitude = requests.get(url, headers=header, params={
									'keys': ['altitude']}).json()

			for r in [latlong, time_list, altitude]:
				if isinstance(r, dict) and 'message' in r.keys():
					check = r['message']
					if check == 'Rate Limit Exceeded':
						print('Rate Limit Exceeded, sleeping for 15 mins')
						self.exceed_counter += 1
						if self.exceed_counter >= 10:
							exit('Over number of daily API requests\nRestart tomorrow')
						sleep(20)
						for i in range(15):
							print(f'Sleep remaining: {int(15-i)} minutes')
							sleep(60)
						print('Recommencing...')
						latlong = requests.get(url, headers=header, params={
											   'keys': ['latlng']}).json()
						time_list = requests.get(url, headers=header, params={
												 'keys': ['time']}).json()
						altitude = requests.get(url, headers=header, params={
												'keys': ['altitude']}).json()
						break

			latlong = latlong[0]['data']
			time_list = time_list[1]['data']
			altitude = altitude[1]['data']

			data = pd.DataFrame([*latlong], columns=['lat', 'long'])
			data['altitude'] = altitude
			start_time = datetime.strptime(start_time, "%Y-%m-%dT%H:%M:%SZ")
			data['time'] = [(start_time + timedelta(seconds=t))
							for t in time_list]

			gpx = gpxpy.gpx.GPX()
			# Create first track in our GPX:
			gpx_track = gpxpy.gpx.GPXTrack()
			gpx.tracks.append(gpx_track)
			# Create first segment in our GPX track:
			gpx_segment = gpxpy.gpx.GPXTrackSegment()
			gpx_track.segments.append(gpx_segment)

			# Create points:
			for idx in data.index:
				gpx_segment.points.append(gpxpy.gpx.GPXTrackPoint(
					data.loc[idx, 'lat'], data.loc[idx, 'long'], elevation=data.loc[idx, 'altitude'], time=data.loc[idx, 'time']))

			with open(f'{self.data_folder}/gpx/{id}.gpx', 'w') as f:
				f.write(gpx.to_xml())
		print('Finished downloading GPX files!')


def main(args):
	helper = StravaApiHelper(args)
	helper.GetUpdatedStravaTokens()
	helper.GetActivitySummary()
	helper.GetGPXFile()

if __name__ == '__main__':
	parser = ArgumentParser(description='Create GPX files from streams downloaded using StravaAPI',
							epilog='Report issues to... ')
	parser.add_argument('--dir', default='n/a',
						help='Current working directory. Data and Keys are specified relative to this.')
	parser.add_argument('--data', default='data',
						help='Data files directory - will contain activity summary and folder of gpx files')
	parser.add_argument('--keys', default='keys',
						help='Folder containing client_info.json and strava_tokens.json')
	args = parser.parse_args()
	main(args)
