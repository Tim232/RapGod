import time
import queue
from threading import Thread
from multiprocessing import Process, Queue, Event

from .. import audio

from .worker import Worker


class ContainedPool:
    def __init__(self, thread_count=1):
        print('Container process for worker pool created')
        self.work_queue = Queue(maxsize=0)
        self.results_queue = Queue(maxsize=0)
        self.thread_count = thread_count
        self.abort = Event()
        self.process_active = False

    def start(self):
        if self.alive():
            return False

        print('Container process starting...')
        self.abort = Event()
        params = (self.work_queue, self.results_queue, self.thread_count,
                  self.abort)
        self.process = Process(target=self._run_thread_pool, args=(params))
        self.process.start()
        self.process_active = True
        return True

    def stop(self, block=True):
        if not self.alive():
            return False

        print('Stopping container process...')
        self.abort.set()

        if block:
            self.process.join(timeout=10)

        self.process_active = False
        print('Container process stopped')
        return True

    def alive(self):
        return self.process_active

    def enqueue(self, task_name, task_args, channel_id):
        self.work_queue.put((task_name, task_args, channel_id))

    def get_result(self):
        return self.results_queue.get(block=False)

    def _run_thread_pool(self, work_queue, results_queue, thread_count, abort):
        pool = ThreadPool(work_queue,
                          results_queue,
                          thread_count=thread_count
                          )
        pool.start()

        try:
            while not abort.is_set():
                time.sleep(1)
        except KeyboardInterrupt:
            pass

        print('Stopping contained pool...')
        pool.stop()
        print('Contained pool stopped')


class ThreadPool:
    def __init__(self, work_queue, results_queue, thread_count=1):
        print(f'Worker pool created with {thread_count} thread(s)')
        self.work_queue = work_queue
        self.results_queue = results_queue
        self.thread_count = thread_count
        self.threads = []
        self.backing_tracks = audio.load_backing_tracks()

    def start(self):
        if self.alive():
            return False

        print('Worker pool starting...')
        self.aborts = []
        self.idles = []
        self.threads = []
        for n in range(self.thread_count):
            abort = Event()
            idle = Event()
            self.aborts.append(abort)
            self.idles.append(idle)
            worker = Worker(f'thread-{n}',
                            self.work_queue,
                            self.results_queue,
                            abort,
                            idle,
                            self.backing_tracks
                            )
            self.threads.append(worker)
        return True

    def stop(self):
        if not self.alive():
            return False

        for abort in self.aborts:
            abort.set()

        for thread in self.threads:
            thread.join()

        print('Worker pool stopped')
        return True

    def alive(self):
        return True in [t.is_alive() for t in self.threads]
