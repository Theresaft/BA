# server/main/routes.py
import time
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS, cross_origin
import redis
from rq import Queue, Connection
from flask import Blueprint, jsonify, request, current_app
import uuid
import os
import shutil
from . import dicom_classifier
import zipfile

from server.main.tasks import preprocessing_task, prediction_task # Note: Since we are inside a docker container we have to adjust the imports accordingly

main_blueprint = Blueprint(
    "main",
    __name__,
)


@main_blueprint.route("/assign-sequence-types", methods=["POST"])
@cross_origin()
def assign_types():
    dicom_base_path = "dicom-images"
    nifti_base_path = "nifti-images"
    unique_id = str(uuid.uuid4())

    dicom_unique_path = os.path.join(dicom_base_path, unique_id)
    nifti_unique_path = os.path.join(nifti_base_path, unique_id)

    # create unique directories
    os.makedirs(dicom_unique_path)
    os.makedirs(nifti_unique_path)

    # extract the zip files to the unique directory
    dicom_sequence = request.files["dicom_data"]

    with zipfile.ZipFile(dicom_sequence) as z:
        z.extractall(dicom_unique_path)

    # run classification
    classification = dicom_classifier.classify(dicom_unique_path)

    return jsonify(classification), 200



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

    with Connection(redis.from_url("redis://redis:6379/0")):
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
    with Connection(redis.from_url("redis://redis:6379/0")):
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



### Dummy route that returns nifti-image (For testing the viewer) 
@main_blueprint.route("/nifti/<id>", methods=["GET"])
def get_nifti(id):
    path = f"/usr/src/app/data/user1/{id}/raw/BRATS_485_0000.nii.gz" # change path to make it work
    print(path)
    try:
        # Send the file to the frontend
        return send_file(path, as_attachment=True, download_name='BRATS_485_0000.nii.gz')
    
    except Exception as e:
        # Handle the error, if the file cannot be served
        return {"error": str(e)}, 500
    