# server/main/routes.py
from flask import request, jsonify, send_file
import redis
from rq import Queue, Connection
from flask import Blueprint, jsonify, request
import uuid
import os
import shutil
from . import dicom_classifier
import zipfile
from server.database import db
from server.main.tasks import preprocessing_task, prediction_task # Note: Since we are inside a docker container we have to adjust the imports accordingly
from server.models import Segmentation, Project, Sequence
import json


main_blueprint = Blueprint(
    "main",
    __name__,
)


@main_blueprint.route("/assign-sequence-types", methods=["POST"])
def assign_types():
    base_path = "temp"
    unique_id = str(uuid.uuid4())

    unique_path = os.path.join(base_path, unique_id)

    # create unique directories
    os.makedirs(unique_path)

    # extract the zip files to the unique directory
    dicom_sequence = request.files["dicom_data"]

    with zipfile.ZipFile(dicom_sequence) as z:
        z.extractall(unique_path)

    # run classification
    classification = dicom_classifier.classify(unique_path)

    shutil.rmtree(unique_path)

    return jsonify(classification), 200



@main_blueprint.route("/predict", methods=["POST"])
def run_task():
    # Get data from request
    segmentation_data = request.get_json()
    user_id = 1 # TODO: Get this from session cookie
    project_id = segmentation_data["project_id"]
    model = "nnunet-model" # TODO: Get this from request


    # TODO: Input Validation

    new_segmentation = Segmentation(
        project_id = project_id,
        t1_sequence = segmentation_data["t1"],
        t1km_sequence = segmentation_data["t1km"],
        t2_sequence = segmentation_data["t2"],
        flair_sequence = segmentation_data["flair"],
        model = model,
        segmentation_name = segmentation_data["segmentation_name"],
    )

    try:
        # Add new segmentation
        db.session.add(new_segmentation)
        db.session.flush()  # Use flush to get segmentation_id
        
        # Create new directory for the segmentation
        segmentation_id = new_segmentation.segmentation_id
        new_segmentation_path = f'/usr/src/image-repository/{user_id}/{project_id}/segmentations/{segmentation_id}'
        os.makedirs(new_segmentation_path)

        # Starting Preprocessing and Prediction Task 
        with Connection(redis.from_url("redis://redis:6379/0")):
            q = Queue("my_queue") # Define the queue
            task_1 = q.enqueue(preprocessing_task, args=[user_id, project_id])  # Preprocessing Task
            task_2 = q.enqueue(prediction_task, depends_on=task_1, args=[user_id, project_id, segmentation_id, model]) # Prediction Task


        preprocessing_id = task_1.get_id()  
        prediction_id = task_2.get_id()  
        print(preprocessing_id)
        print(prediction_id)

        # Update segmentation object and commit to DB
        new_segmentation.preprocessing_id = task_1.get_id()  
        new_segmentation.prediction_id = task_2.get_id()  
        db.session.commit()

        return jsonify({'message': 'Jobs started successfully!', 'preprocessing_id': task_1.id, 'prediction_id': task_2.id, 'segmentation_id': segmentation_id}), 202

    except Exception as e:
        db.session.rollback()
        return jsonify({'message': f'Error occurred while creating starting prediction: {str(e)}'}), 500



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
    path = f"/usr/src/image-repository/1/1/raw/BRATS_485_0000.nii.gz" # change path to make it work
    try:
        # Send the file to the frontend
        return send_file(path, as_attachment=True, download_name='BRATS_485_0000.nii.gz')
    
    except Exception as e:
        # Handle the error, if the file cannot be served
        return {"error": str(e)}, 500
    


@main_blueprint.route("/projects", methods=["POST"])
def create_project():
    project_name = request.form.get("project_name")
    stringified_file_infos = request.form.get("file_infos")
    file_infos = json.loads(stringified_file_infos)
    files = request.files["dicom_data"]
    user_id = "1"  # TODO: Get user ID from session cookie

    # TODO: All kinds of Validations

    # Create new project object
    new_project = Project(
        user_id=user_id,
        project_name=project_name
    )

    sequence_ids = []

    # Save new project in the database
    try:
        db.session.add(new_project)
        db.session.flush()  # Use flush to get project_id before committing

        # Retrieve project_id from the new_project object after flush
        project_id = new_project.project_id

        # Create folder structure for project
        project_path = f'/usr/src/image-repository/{user_id}/{project_id}'
        raw_directory = os.path.join(f'{project_path}/raw')
        preprocessed_directory = os.path.join(f'{project_path}/preprocessed')
        segmentations_directory = os.path.join(f'{project_path}/segmentations')
        os.makedirs(raw_directory, exist_ok=False)
        os.makedirs(preprocessed_directory, exist_ok=False)
        os.makedirs(segmentations_directory, exist_ok=False)

        # Add all sequences to the database
        for sequence_data in file_infos:
            sequence_name = sequence_data.get('sequence_name')
            sequence_type = sequence_data.get('sequence_type')

            # Create new sequence object
            new_sequence = Sequence(
                project_id=project_id,
                sequence_name=sequence_name,
                sequence_type=sequence_type,
                preprocessed_flag=False
            )

            # Add sequence
            db.session.add(new_sequence)
            db.session.flush()

            # Retrive sequence_id
            sequence_id = new_sequence.sequence_id

            sequence_ids.append({
                "name": sequence_name,
                "id": sequence_id
            })

            # Create sequence folder
            sequence_directory = os.path.join(f'{raw_directory}/{sequence_id}')
            os.makedirs(sequence_directory, exist_ok=False)

            # Extract dicom files to the correct folder
            with zipfile.ZipFile(files) as z:
                # List all files in the zip archive
                for file in z.namelist():
                    # Check if the file is in the desired sub-folder
                    if file.startswith(sequence_name):
                        filename = os.path.basename(file)
                        # skip directories
                        if not filename:
                            continue
                    
                        # copy file to the correct destination
                        source = z.open(file)
                        target = open(os.path.join(sequence_directory, filename), "wb")
                        with source, target:
                            shutil.copyfileobj(source, target)


        # Commit project and sequences to the database
        db.session.commit()

        return jsonify({'message': 'Project and sequences created successfully!', "project_id": project_id, "sequence_ids": sequence_ids}), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({'message': f'Error occurred while creating the project: {str(e)}'}), 500
    


@main_blueprint.route("/uploadSequenceTypes", methods=["POST"])
def assign_sequence_types():
    try:
        # Get data from request
        sequence_types = request.get_json()

        # Assign sequence types to database
        for sequence in sequence_types:
            print(sequence)
            sequence_entry = db.session.query(Sequence).filter_by(sequence_id=sequence["sequence_id"]).first()
            sequence_entry.sequence_type = sequence["sequence_type"]
        
        db.session.commit()

        return jsonify({'message': 'Sequence types sucessfully uploaded!'}), 200
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': f'Error occurred while updating sequence types: {str(e)}'}), 500