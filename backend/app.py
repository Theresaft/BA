# app.py
import redis
from rq import Connection, Worker
from flask.cli import FlaskGroup
from flask import Flask, request, jsonify
from server import create_app
from werkzeug.security import check_password_hash
from bson.objectid import ObjectId


app = create_app()
cli = FlaskGroup(create_app=create_app)


# Initialize Worker
@cli.command("run_worker")
def run_worker():
    redis_url = app.config["REDIS_URL"]
    redis_connection = redis.from_url(redis_url)
    with Connection(redis_connection):
        worker = Worker(app.config["QUEUES"])
        worker.work()

if __name__ == "__main__":
    cli()
