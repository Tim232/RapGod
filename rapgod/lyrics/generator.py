import os
import re
import random

import tswift

from .context import Context

class Generator:
    def __init__(self, songs):
        self.songs = songs

    def generate_lyrics(self, word, lines=20):
        song = random.choice(self.songs)
        song = tswift.Song(*song)

        verses = self.parse_lyrics(song.lyrics)

        content = []
        for verse in verses:
            content.extend(verse)
            if len(content) > lines:
                break

        lyrics = []
        for line in content:
            ctx = Context(line)
            nouns = list(ctx.nouns())
            if len(nouns) > 0:
                random.choice(nouns).set(word)

            part = ctx.generate()
            if not re.search(r'[,.?!]$', part):
                part += ','
            lyrics.append(part)

        return '\n'.join(lyrics)

    def parse_lyrics(self, lyrics, clean = True):
        if clean:
            lyrics = re.sub('\[.*\]', '', lyrics)
            lyrics = lyrics.strip()

        verses = re.split('\n\n+', lyrics)
        verses = [line.split('\n') for line in verses]

        return verses
