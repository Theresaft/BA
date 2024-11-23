import redis
from rq import Connection, Worker
from multiprocessing import Process

REDIS_URL = "redis://redis:6379/0"
QUEUES = ["my_queue"]

# Initialize Worker
def run_worker():
    redis_connection = redis.from_url(REDIS_URL)
    with Connection(redis_connection):
        worker = Worker(QUEUES)
        worker.work()

if __name__ == "__main__":

    number_of_workers = 4 # TODO: Set to number of available GPUs?

    for i in range(number_of_workers):  
        worker = Process(target=run_worker)
        worker.start()

# Alternativ könnte man auch die worker container skalieren: docker-compose up --scale worker=2