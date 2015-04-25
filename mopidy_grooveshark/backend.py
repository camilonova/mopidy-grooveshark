# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import pykka

from urlparse import urlparse
from multiprocessing.pool import ThreadPool

from mopidy import backend
from mopidy.models import Track
from mopidy.models import Album
from mopidy.models import SearchResult

from grooveshark import Client
from mopidy_grooveshark import logger


def get_track(song):
    """
    Returns a Mopidy track from a Grooveshark song object.
    """
    try:
        length = int(song.duration.split('.')[0]) * 1000
        if length == 0:
            logger.debug("Grooveshark report 0 duration for: %s", song)
            return None

        return Track(
            name=song.name,
            comment=song.artist.name,
            length=length,
            album=Album(
                name=song.album.name,
                images=[song.album.cover._url]
            ),
            uri=song.stream.url,
        )
    except TypeError:
        logger.debug("Grooveshark API error for: %s", song)
        return None


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

    return [song for song in playlist if song]


def search_grooveshark(query):
    """
    Makes a search on Grooveshark and return the songs.
    """
    logger.debug("Searching Grooveshark for: '%s'", query)

    client = Client()
    client.init()

    resolve_pool = ThreadPool(processes=16)
    track_list = resolve_pool.map(get_track, client.search(query))
    resolve_pool.close()

    return [song for song in track_list if song]


class GroovesharkBackend(pykka.ThreadingActor, backend.Backend):

    def __init__(self, config, audio):
        super(GroovesharkBackend, self).__init__()
        self.config = config
        self.uri_schemes = ['grooveshark', 'gs']
        self.library = GroovesharkLibraryProvider(backend=self)


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

    def search(self, query=None, uris=None, exact=False):
        return SearchResult(
            uri='grooveshark:search',
            tracks=search_grooveshark(' '.join(query.values()[0])),
        )
