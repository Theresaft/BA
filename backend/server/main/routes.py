# server/main/routes.py
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS, cross_origin
import redis
from rq import Queue, Connection
from flask import Blueprint, jsonify, request, current_app
import uuid
import os
import shutil
# import dicom_classifier

from server.main.tasks import preprocessing_task, prediction_task # Note: Since we are inside a docker container we have to adjust the imports accordingly

main_blueprint = Blueprint(
    "main",
    __name__,
)

app = Flask(__name__)
CORS(app)  # Allow CORS for all routes
app.config['CORS_HEADERS'] = 'Content-Type'


@main_blueprint.route("/assign-sequence-types", methods=["POST"])
@cross_origin()
def assign_types():
    # Input: DICOM Headers for every sequence 
    # TODO: Analyse DICOM Headers and
        # 1. Assign a Type to each sequence (t1, t2, ...)
        # 2. Choose the best sequence of every type
    # Return: Send back JSON with all assigned types for every sequence and mark the best ones
    # request.json() contains all the info needed in the same object format as in the frontend. The entire
    # payload is contained, so that information can be used to extract the DICOM headers.
    return request.get_json()



#@main_blueprint.route("/predict-segmentation", methods=["POST"])
#def predict_segmentation():
    # Input: 4 DICOM Sequences (t1, t2, ...) and the selected model 
    # TODO:
        # 1. Convert DICOM to Nifti
        # 2. Queue Preprocessing Job
        # 3. Queue Prediction Job for the given model
        # 4. Create DB entry for Result (include both Job IDs, chosen model)
    # Return: Job started successful
#    return


#@main_blueprint.route("/predict-again", methods=["POST"])
#def predict_segmentation():
    # Input: ID/Reference to a past prediction and the selected model
    # TODO:
        # 1. Queue Prediction Job
        # 2. Create DB entry (include Job ID) 
    # Return: Job started successful    
#    return






#### Example of a Queue ####


@main_blueprint.route("/tasks", methods=["POST"])
def run_task():
    #task_type = request.form["type"]

    with Connection(redis.from_url(current_app.config["REDIS_URL"])):
        q = Queue("my_queue") # Define the queue
        unique_id = str(uuid.uuid4()) 
        
        # Create Directory for Raw Data 
        raw_data_path = f'/usr/src/app/data/user1/{unique_id}/raw' 
        os.makedirs(raw_data_path, exist_ok=True) 


        # Simulates saving the data from request to the raw directory (actually only copys data from test_data to raw)
        fake_request_data = '/usr/src/app/data/test_data'
        for item in os.listdir(fake_request_data):
            s = os.path.join(fake_request_data, item)
            d = os.path.join(raw_data_path, item)
            if os.path.isfile(s):  
                shutil.copy2(s, d)

        # Preprocessing Task
        task_1 = q.enqueue(preprocessing_task, unique_id)

        # Prediction Task
        task_2 = q.enqueue(prediction_task, depends_on=task_1, args=[unique_id])

        response_object = {
            "status": "success",
            "data": {
                "unique_id" : unique_id,
                "task_1_id": task_1.get_id(),
                "task_2_id": task_2.get_id()
            },
        }

    return jsonify(response_object), 202


@main_blueprint.route("/tasks/<task_id>", methods=["GET"])
def get_status(task_id):
    with Connection(redis.from_url(current_app.config["REDIS_URL"])):
        q = Queue("my_queue")
        task = q.fetch_job(task_id)
    if task:
        response_object = {
            "status": "success",
            "data": {
                "task_id": task.get_id(),
                "task_status": task.get_status(),
                "task_result": task.result,
            },
        }
    else:
        response_object = {"status": "error"}
    return jsonify(response_object)
