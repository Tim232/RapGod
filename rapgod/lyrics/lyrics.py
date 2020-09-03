import os
import json
import argparse

import tswift

from .generator import Generator

CONFIG = 'config/songs.json'

CACHE = 'cache/'
SONG_CACHE = os.path.join(CACHE, 'songs.json')

def main():
    parser = argparse.ArgumentParser(description='command line to generate weird lyrics')
    parser.add_argument('word', help='word to make the song about')
    parser.add_argument('--force-reload', action='store_true',
            help='force rebuild the songs cache')
    args = parser.parse_args()

    songs = load_songs(args.force_reload)
    gen = Generator(songs)

    lyrics = gen.generate_lyrics(args.word)
    print(lyrics)

def load_songs(force_reload=False):
    with open(CONFIG) as f:
        config = json.load(f)

    if force_reload or not os.path.exists(SONG_CACHE) or os.path.getmtime(CONFIG) > os.path.getmtime(SONG_CACHE):
        os.makedirs(CACHE, exist_ok = True)

        cache = []
        for artist, songs in config.items():
            if isinstance(songs, str):
                if songs == '*':
                    # all songs by artist
                    cache.extend((song.title, artist) for song in tswift.Artist(artist).songs)
                else:
                    # only one song by artist
                    cache.append((songs, artist))
            else:
                # multiple songs by artist
                cache.extend((song, artist) for song in songs)

        with open(SONG_CACHE, 'w') as f:
            json.dump(cache, f, indent=4)
    else:
        with open(SONG_CACHE) as f:
            cache = json.load(f)

    return cache
