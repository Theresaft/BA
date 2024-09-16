import redis
from rq import Connection, Worker


REDIS_URL = "redis://redis:6379/0"
QUEUES = ["my_queue"]

# Initialize Worker
def run_worker():
    redis_connection = redis.from_url(REDIS_URL)
    with Connection(redis_connection):
        worker = Worker(QUEUES)
        worker.work()
    
run_worker()