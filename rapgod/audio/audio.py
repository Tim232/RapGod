import os
import random
from io import BytesIO
from pydub import AudioSegment
from pydub import effects
from google.cloud import texttospeech
from google.oauth2 import service_account

OFFSET_MS = 15000
TRACKS_DIR = 'static/audio'


def init():
    global tts_client
    credentials = service_account.Credentials.from_service_account_file(
        'config/google_cloud_key.json')
    tts_client = texttospeech.TextToSpeechClient(credentials=credentials)


def load_backing_tracks():
    backing_tracks = []
    track_names = os.listdir(TRACKS_DIR)

    print("Loading backing tracks...")
    for name in track_names:
        print(f'↳ Load & normalize \'{name}\'')
        track = AudioSegment.from_mp3(f'static/audio/{name}')
        track = effects.normalize(track, headroom=6)
        backing_tracks.append(track)
    print("Done")

    return backing_tracks


def make_stream(text, backing_track, format):
    # Running speech synthesis...
    synthesis_input = texttospeech.types.SynthesisInput(text=text)

    voice = texttospeech.types.VoiceSelectionParams(
        language_code='en-US',
        name='en-US-Wavenet-D')

    audio_config = texttospeech.types.AudioConfig(
        audio_encoding=texttospeech.enums.AudioEncoding.MP3,
        speaking_rate=0.93,
        pitch=-6.0)

    response = tts_client.synthesize_speech(synthesis_input, voice,
                                            audio_config)

    # Processing result...
    voice_buffer = BytesIO(response.audio_content)
    voice_track = AudioSegment.from_mp3(voice_buffer)
    voice_track = voice_track.set_frame_rate(96000)

    # Mixing tracks...
    output_track = backing_track.overlay(voice_track, position=OFFSET_MS)
    output_track = output_track.set_frame_rate(48000)

    # Trim output track to end when vocals end
    output_track = output_track[:len(voice_track) + OFFSET_MS]

    # Encoding...
    buffer = BytesIO()
    output_track.export(buffer, format=format)
    buffer.seek(0)

    return buffer


def mp3_encode_stream(stream):
    track = AudioSegment.from_raw(
        stream,
        sample_width=2,
        frame_rate=48000,
        channels=2
    )

    mp3_stream = BytesIO()
    track.export(mp3_stream, format='mp3')
    return mp3_stream
