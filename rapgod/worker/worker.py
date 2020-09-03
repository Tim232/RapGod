import time
import queue
import random
from threading import Thread

from .. import lyrics
from .. import audio


class Worker(Thread):
    def __init__(self, name, queue, results, abort, idle, backing_tracks):
        Thread.__init__(self)
        self.name = name
        self.daemon = True

        audio.init()
        self.abort = abort
        self.idle = idle
        self.work_queue = queue
        self.results_queue = results
        self.generator = lyrics.Generator(lyrics.load_songs())
        self.backing_tracks = backing_tracks

        self.start()

    def run(self):
        print(f'{self.name}: Awake')
        while not self.abort.is_set():
            try:
                work = self.work_queue.get(timeout=1)
                self.idle.clear()
                self.do_work(work)
            except queue.Empty:
                self.idle.set()

        print(f'{self.name}: Exiting')

    def do_work(self, work):
        start = time.time()
        task_name, task_args, channel_id = work

        print(f'{self.name}: Running \'{task_name}\'...')

        if task_name == 'gen_lyrics':
            result = self.gen_lyrics(task_args)
        elif task_name == 'make_pcm_track':
            result = self.make_track(task_args, 's16le')
        elif task_name == 'make_mp3_track':
            result = self.make_track(task_args, 'mp3')
        elif task_name == 'pcm_to_mp3':
            result = self.convert_track(task_args)
        else:
            print(f'Unknown task name \'{task_name}\'')
            return

        self.results_queue.put((task_name, result, channel_id))

        end = time.time()
        print(f'{self.name}: Done [{end - start}s]')

    def gen_lyrics(self, theme_words):
        return self.generator.generate_lyrics(theme_words)

    def make_track(self, theme_words, format):
        lyrics = self.gen_lyrics(theme_words)
        backing_track = random.choice(self.backing_tracks)
        return audio.make_stream(lyrics, backing_track, format)

    def convert_track(self, stream):
        return audio.mp3_encode_stream(stream)
