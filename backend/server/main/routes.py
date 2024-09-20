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


main_blueprint = Blueprint(
    "main",
    __name__,
)


@main_blueprint.route("/assign-sequence-types", methods=["POST"])
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



@main_blueprint.route("/predict", methods=["POST"])
def run_task():
    user_id = 1 # TODO: Get this from session cookie
    project_id = 1  # TODO: Get this from request
    model = "nnunet-model" # TODO: Get this from request


    # TODO: Input Validation

    new_segmentation = Segmentation(
        project_id = project_id,
        t1_sequence = 1, # TODO: Add real sequences that were selected
        t1km_sequence = 2,
        t2_sequence = 3,
        flair_sequence = 4,
        model = model,
        segmentation_name ="My Segmentation",
    )

    try:
        # Add new segmentation
        db.session.add(new_segmentation)
        db.session.flush()  # Use flush to get segmentation_id
        
        # Create new directory for the segmentation
        segmentation_id = new_segmentation.segmentation_id
        new_segmentation_path = f'/usr/src/app/image-repository/{user_id}/{project_id}/segmentations/{segmentation_id}'
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

        return jsonify({'message': 'Jobs started successfully!', 'preprocessing_id': task_1.id, 'prediction_id': task_2.id}), 202

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
    path = f"/usr/src/app/image-repository/1/1/raw/BRATS_485_0000.nii.gz" # change path to make it work
    try:
        # Send the file to the frontend
        return send_file(path, as_attachment=True, download_name='BRATS_485_0000.nii.gz')
    
    except Exception as e:
        # Handle the error, if the file cannot be served
        return {"error": str(e)}, 500
    


@main_blueprint.route("/projects", methods=["POST"])
def create_project():
    data = request.get_json()
    project_name = data.get('project_name', '').strip()
    sequences = data.get('sequences', [])

    user_id = "1"  # TODO: Get user ID from session cookie


    # TODO: All kinds of Validations

    # Create new project object
    new_project = Project(
        user_id=user_id,
        project_name=project_name
    )


    # Save new project in the database
    try:
        db.session.add(new_project)
        db.session.flush()  # Use flush to get project_id before committing

        # Retrieve project_id from the new_project object after flush
        project_id = new_project.project_id

        # Add all sequences to the database
        for sequence_data in sequences:
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

        # Create folder structure for project
        project_path = f'/usr/src/app/image-repository/{user_id}/{project_id}'
        raw_directory = os.path.join(f'{project_path}/raw') 
        preprocessed_directory = os.path.join(f'{project_path}/preprocessed') 
        segmentations_directory = os.path.join(f'{project_path}/segmentations') 
        os.makedirs(raw_directory, exist_ok=False) 
        os.makedirs(preprocessed_directory, exist_ok=False) 
        os.makedirs(segmentations_directory, exist_ok=False) 

        # Commit project and sequences to the database
        db.session.commit()

        return jsonify({'message': 'Project and sequences created successfully!'}), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({'message': f'Error occurred while creating the project: {str(e)}'}), 500