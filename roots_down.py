# Imports - requires Spotipy
import requests
import numpy as np
import datetime as dt
import spotipy
import spotipy.util as util
import pandas as pd
# needed for authorization but cleint_secret should not be made public, stored in a separate file anme user_details
from user_details import client_id, client_secret, base_url, url_end

# URL and dates for NPR AJAX song database access 
last_day	= dt.datetime.today() #latest Roots Down playlist to create
first_day	= dt.datetime(2017,1,1) #earliest Roots Down playlist to create
date_arr	= pd.date_range(start=first_day, end=last_day, freq='W')
date_arr	= [day.strftime('%Y-%m-%d') for day in date_arr]

# Spotify search parameters details
redirect_uri	= 'http://127.0.0.1/callback'
scope			= 'playlist-modify-public'
user_id			= 'davidstauffer'

# remove paratheses
# track_name: string for name of track
def modify_track(track_name):
	return track_name.split(' (', 1)[0]

# take first two words
#artist_name: string of artist's name
def modify_artist(artist_name):
	return ' '.join(artist_name.split(' ', 2)[0:2])

# search for track on spotify
# sp: Spotify object created by the Spotipy library
# search_text: string to search with
def lookup_track(sp, search_text):
	results = sp.search(track_name, limit=10, offset=0, type='track', market=None)['tracks']['items']
	return results[0] if len(results) > 0 else None

# add a list of track ids to a Spotify playlist by id
# sp: Spotify object created by the Spotipy library
# playlist_id: string id for playlist
# track_ids: list of string song ids
def add_tracks_to_playlist(sp, playlist_id, track_ids):
	sp.user_playlist_add_tracks(user_id, playlist_id, track_ids)

# Start of the real action
# Get authorization for this code to access your Spotify app.
# Requires creating a Spotify app and registering to use the API
# can be done at (as of 1/1/2017): https://developer.spotify.com/my-applications/#!/applications
# set up a redirect URI: http://127.0.0.1/callback
token = util.prompt_for_user_token(user_id, scope=scope, client_id=client_id, client_secret=client_secret, redirect_uri=redirect_uri)


if token:
	sp = spotipy.Spotify(auth=token)
	sp.trace = False
else:
	raise LookupError(user_id)

skipped_songs = 0
found_songs   = 0
# build a list of the users current playlists
offset = 0
current_playlists = sp.current_user_playlists(limit=50, offset = 0)['items']
next_list = current_playlists
while len(next_list) == 50:
	next_list = sp.current_user_playlists(limit=50, offset=len(current_playlists))['items']
	current_playlists = current_playlists + next_list
current_playlist_names	= [playlist['name'] for playlist in current_playlists]


for date in date_arr:
	# Get playlist from NPR database
	response				= requests.get(base_url + date + url_end)
	response.raise_for_status() # raise exception if invalid response
	playlist_obj			= response.json()['playlist'][0]
	spotify_date			= playlist_obj['date']
	print(spotify_date)
	spotify_date			= spotify_date.replace('-','/')
	spotify_playlist_name	= 'Roots Down - ' + spotify_date
	print(spotify_playlist_name)

	print('Attempting playlist: ' + spotify_playlist_name)

	#check if playlist already exists, if so continue to next loop iteration
	if spotify_playlist_name in current_playlist_names:
		print('Already done: ' + spotify_playlist_name)
		continue

	#create spotify playlist
	playlist	= sp.user_playlist_create(user_id, spotify_playlist_name)
	playlist_id	= playlist['id']

	tracks		= []

	for song_obj in playlist_obj['playlist']:
		track_name	= song_obj['trackName']
		artist_name	= song_obj['artistName']
		album_name	= song_obj['collectionName'] if 'collectionName' in song_obj.keys() else ''

		song_search	= lookup_track(sp, track_name + ' ' + artist_name + ' ' + album_name)
		if song_search:
			tracks.append(song_search['id'])
		else:
			song_search	= lookup_track(sp, track_name + ' ' + artist_name)
			if song_search:
				tracks.append(song_search['id'])
			else: 
				song_search	= lookup_track(sp, modify_track(track_name) + ' ' + modify_artist(artist_name ))
				if song_search:
					tracks.append(song_search['id'])
				else:
					skipped_songs += 1
	found_songs += len(tracks)
	add_tracks_to_playlist(sp, playlist_id, tracks)

print('Number of skipped songs: ' + str(skipped_songs))
print('Number of songs found: ' + str(found_songs))
print('Number of Roots Down playlists in given range: ' + str(len(date_arr)))

