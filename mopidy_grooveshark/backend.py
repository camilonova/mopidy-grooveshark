# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from urlparse import urlparse
# import re
# import string
from multiprocessing.pool import ThreadPool
# from urlparse import urlparse, parse_qs
# import unicodedata

# import pafy

from mopidy import backend
from mopidy.models import Track
from mopidy.models import Album
# from mopidy.models import SearchResult, Track, Album
import pykka
# import requests
from mopidy_grooveshark import logger

from grooveshark import Client


def get_track(song):
    """
    Returns a Mopidy track from a Grooveshark song object.
    """
    return Track(
        name=song.name,
        comment=song.artist.name,
        length=int(song.duration) * 1000,
        album=Album(
            name=song.album.name,
            images=[song.album.cover._url]
        ),
        uri=song.stream.url,
    )


def play_a_song(uri):
    """
    Play a song from Grooveshark. Needs to have a token.

    http://grooveshark.com/s/Because+Of+You/4DYDAi

    Token: 4DYDAi
    """
    logger.debug("Playing Grooveshark Song '%s'", uri)

    # Get token from uri
    token = urlparse(uri).path.split('?')[0].split('/')[-1]

    client = Client()
    client.init()

    song = client.get_song_by_token(token)

    return get_track(song)


def play_a_playlist(uri):
    """
    Play a playlist from Grooveshark.

    http://grooveshark.com/playlist/Office+Hours+Jazz/19537110

    Playlist ID: 19537110
    """
    logger.debug("Playing Grooveshark Playlist '%s'", uri)

    # Get playlist_id from uri
    playlist_id = urlparse(uri).path.split('?')[0].split('/')[-1]

    client = Client()
    client.init()

    playlist = client.playlist(playlist_id)
    resolve_pool = ThreadPool(processes=16)
    playlist = resolve_pool.map(get_track, playlist.songs)
    resolve_pool.close()

    return playlist


# FIXME: Seems is never used
def resolve_track(track, stream=False):
    logger.debug("Resolving Grooveshark for track '%s'", track)
    if hasattr(track, 'uri'):
        return resolve_url(track.comment, stream)
    else:
        return resolve_url(track.split('.')[-1], stream)


# FIXME: Seems is never used
def resolve_url(url, stream=False):
    # try:
    #     video = pafy.new(url)
    #     if not stream:
    #         uri = 'youtube:video/%s.%s' % (
    #             safe_url(video.title), video.videoid
    #         )
    #     else:
    #         uri = video.getbestaudio()
    #         if not uri:  # get video url
    #             uri = video.getbest()
    #         logger.debug('%s - %s %s %s' % (
    #             video.title, uri.bitrate, uri.mediatype, uri.extension))
    #         uri = uri.url
    #     if not uri:
    #         return
    # except Exception as e:
    #     # Video is private or doesn't exist
    #     logger.info(e.message)
    #     return

    from grooveshark import Client
    client = Client()
    client.init()
    # client.get_song_by_token('78fUgO')
    # TODO: change the name from url to token
    song = client.get_song_by_token(url)

    track = Track(
        name=song.name,
        comment=song.artist.name,
        length=song.duration * 1000,
        album=Album(
            name=song.album.name,
            images=[song.album.cover._url]
        ),
        uri=song.stream.url,
    )

    return track


# def search_youtube(q):
#     query = {
#         'part': 'id',
#         'maxResults': 15,
#         'type': 'video',
#         'q': q,
#         'key': yt_key
#     }
#     result = session.get(yt_api_endpoint+'search', params=query)
#     data = result.json()

#     resolve_pool = ThreadPool(processes=16)
#     playlist = [item['id']['videoId'] for item in data['items']]

#     playlist = resolve_pool.map(resolve_url, playlist)
#     resolve_pool.close()
#     return [item for item in playlist if item]


# def resolve_playlist(url):
#     resolve_pool = ThreadPool(processes=16)
#     logger.info("Resolving Youtube-Playlist '%s'", url)
#     playlist = []

#     page = 'first'
#     while page:
#         params = {
#             'playlistId': url,
#             'maxResults': 50,
#             'key': yt_key,
#             'part': 'contentDetails'
#         }
#         if page and page != "first":
#             logger.debug("Get Youtube-Playlist '%s' page %s", url, page)
#             params['pageToken'] = page

#         result = session.get(yt_api_endpoint+'playlistItems', params=params)
#         data = result.json()
#         page = data.get('nextPageToken')

#         for item in data["items"]:
#             video_id = item['contentDetails']['videoId']
#             playlist.append(video_id)

#     playlist = resolve_pool.map(resolve_url, playlist)
#     resolve_pool.close()
#     return [item for item in playlist if item]


class GroovesharkBackend(pykka.ThreadingActor, backend.Backend):

    def __init__(self, config, audio):
        super(GroovesharkBackend, self).__init__()
        self.config = config
        self.uri_schemes = ['grooveshark', 'gs']
        self.library = GroovesharkLibraryProvider(backend=self)
        self.playback = GroovesharkPlaybackProvider(audio=audio, backend=self)


class GroovesharkLibraryProvider(backend.LibraryProvider):
    def lookup(self, uri):
        # Clean the prefix
        if uri.startswith('gs:'):
            uri = uri[3:]
        elif uri.startswith('grooveshark:'):
            uri = uri[12:]

        # Remove hashbang
        if '/#!' in uri:
            uri = uri.replace('/#!', '')

        # Play a song or playlist
        if '//grooveshark.com/s/' in uri:
            return [play_a_song(uri)]
        elif '//grooveshark.com/playlist/' in uri:
            return play_a_playlist(uri)


#     def search(self, query=None, uris=None, exact=False):
#         # TODO Support exact search

#         if not query:
#             return

#         if 'uri' in query:
#             search_query = ''.join(query['uri'])
#             url = urlparse(search_query)
#             if 'youtube.com' in url.netloc:
#                 req = parse_qs(url.query)
#                 if 'list' in req:
#                     return SearchResult(
#                         uri='youtube:search',
#                         tracks=resolve_playlist(req.get('list')[0])
#                     )
#                 else:
#                     logger.info(
#                         "Resolving Youtube for track '%s'", search_query)
#                     return SearchResult(
#                         uri='youtube:search',
#                         tracks=[resolve_url(search_query)]
#                     )
#         else:
#             search_query = ' '.join(query.values()[0])
#             logger.info("Searching Youtube for query '%s'", search_query)
#             return SearchResult(
#                 uri='youtube:search',
#                 tracks=search_youtube(search_query)
#             )


# TODO: Find when this is used
class GroovesharkPlaybackProvider(backend.PlaybackProvider):

    def translate_uri(self, uri):
        # FIXME: stream is always True, seems fine to remove it.
        track = resolve_track(uri, True)
        if track is not None:
            return track.uri
        else:
            return None
