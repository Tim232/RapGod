import time

if __name__ == "__main__":
    from . import ContainedPool

    pool = ContainedPool(thread_count=4)
    pool.start()

    for i in range(20):
        pool.enqueue("test", i)

    time.sleep(10)

    pool.stop()
    print("Pool stopped, ending program")
