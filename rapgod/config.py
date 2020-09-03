import os
import sys
import json

DISCORD_CONFIG_PATH = 'config/discord.json'
VOICE_CHANNEL_CONFIG_PATH = 'config/voice_channel_map.json'
LYRICS_CHANNEL_CONFIG_PATH = 'config/lyrics_channel_map.json'


def load_config():
    global token, command_prefix, thread_count, voice_channel_map
    global lyrics_channel_map

    print('Loading config files...')
    try:
        with open(DISCORD_CONFIG_PATH) as file:
            try:
                config = json.load(file)
            except json.decoder.JSONDecodeError:
                die(f'Cannot parse {DISCORD_CONFIG_PATH}')

            try:
                token = config['token']
                command_prefix = config['command_prefix']
                thread_count = config['thread_count']
            except KeyError:
                fatal(f'Cannot find required keys in {DISCORD_CONFIG_PATH}\
                      \nSee README.md for required structure')
    except OSError:
        fatal('Cannot open discord.json config file')

    try:
        with open(VOICE_CHANNEL_CONFIG_PATH) as file:
            print('Using existing voice_channel_map')
            try:
                voice_channel_map = json.load(file)
            except json.decoder.JSONDecodeError:
                fatal(f'Cannot parse {VOICE_CHANNEL_CONFIG_PATH}\
                      \nTry deleting the file')
    except OSError:
        print('Creating empty voice_channel_map')
        voice_channel_map = {}

    try:
        with open(LYRICS_CHANNEL_CONFIG_PATH) as file:
            print('Using existing lyrics_channel_map')
            try:
                lyrics_channel_map = json.load(file)
            except json.decoder.JSONDecodeError:
                fatal(f'Cannot parse {LYRICS_CHANNEL_CONFIG_PATH}\
                      \nTry deleting the file')
    except OSError:
        print('Creating empty lyrics_channel_map')
        lyrics_channel_map = {}


def save_voice_channel_map():
    try:
        with open(VOICE_CHANNEL_CONFIG_PATH, 'w') as file:
            json.dump(voice_channel_map, file)
            print('Saved voice_channel_map')
    except OSError:
        print(f'Cannot save to {VOICE_CHANNEL_CONFIG_PATH}')


def save_lyrics_channel_map():
    try:
        with open(LYRICS_CHANNEL_CONFIG_PATH, 'w') as file:
            json.dump(lyrics_channel_map, file)
            print('Saved lyrics_channel_map')
    except OSError:
        print(f'Cannot save to {LYRICS_CHANNEL_CONFIG_PATH}')


def fatal(message):
    print(message)
    sys.exit(1)
