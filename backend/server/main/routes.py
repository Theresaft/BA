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
from io import BytesIO
from pathlib import Path


main_blueprint = Blueprint(
    "main",
    __name__,
)


@main_blueprint.route("/classify", methods=["POST"])
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


# This endpoint returns a zip file containing all images for a segmentation including the raw images.
# The zip includes four subdirectories (`t1`, `t1km`, `t2`, `flair`), each containing either NIfTI or DICOM files,
# and three NIfTI label files (`label_1.nii.gz`, `label_2.nii.gz`, `label_3.nii.gz`) in the root.
@main_blueprint.route("/projects/<project_id>/segmentations/<segmentation_id>", methods=["GET"])
def get_segmentation(project_id, segmentation_id):
    user_id = 1 # TODO: Get this from session cookie

    # TODO: Check if Segmentaion belongs to user and exists
    segmentation = Segmentation.query.filter_by(project_id=project_id, segmentation_id=segmentation_id).first()
   
    # All paths for files to include in the zip
    raw_path = f'/usr/src/image-repository/{user_id}/{project_id}/raw'
    t1_path = Path(f'{raw_path}/{segmentation.t1_sequence}')
    t1km_path = Path(f'{raw_path}/{segmentation.t1km_sequence}')
    t2_path = Path(f'{raw_path}/{segmentation.t2_sequence}')
    flair_path = Path(f'{raw_path}/{segmentation.flair_sequence}')
    segmentations_path = Path(f'/usr/src/image-repository/{user_id}/{project_id}/segmentations/{segmentation_id}')

    # Create the zip file in memory
    memory_file = BytesIO()
    with zipfile.ZipFile(memory_file, 'w', zipfile.ZIP_DEFLATED) as zipf:
        # Add all sequences into a separate directory 
        for directory, folder_name in [(t1_path, 't1'), (t1km_path, 't1km'), (t2_path, 't2'), (flair_path, 'flair')]:
            if directory.exists() and directory.is_dir():
                for file in directory.glob('*.*'):
                    zipf.write(file, arcname=f'{folder_name}/{file.name}')

        # Add label files to the root directory of the zip
        for label_file in segmentations_path.glob('*.nii.gz*'):  
            if label_file.exists():
                zipf.write(label_file, arcname=label_file.name)

    memory_file.seek(0)

    # Return the zip file
    response = send_file(
        memory_file,
        mimetype='application/zip',
        download_name='imaging_files.zip',
        as_attachment=True
    )

    # Add a header indicating if files are DICOM or NIFTI
    # TODO: Save in DB if Files are DICOM or NIFTI
    response.headers['X-File-Type'] = "DICOM"  #"NIFTI"

    return response


# Returns all relevant informations on all projects of the user except the actual sequences
@main_blueprint.route("/projects", methods=["GET"])
def get_projects():
    user_id = 1 # TODO: Get this from session cookie

    # Get all projects from a given user
    projects = Project.query.filter_by(user_id = user_id)

    response = []
    
    for project in projects:
        project_id = project.project_id

        # Create an object for each project
        project_info = {
            "projectID" : project_id,
            "projectName" : project.project_name,
            "sequences" : [],
            "segmentations" : []
        }

        # Get all sequences of the project
        sequences = Sequence.query.filter_by(project_id = project_id)

        for sequence in sequences:
            # Create an object for each sequence in the project
            sequence_info = {
                "sequenceID" : sequence.sequence_id,
                "sequenceName" : sequence.sequence_name,
                "sequenceType" : sequence.sequence_type,
                "classifiedSequenceType" : sequence.classified_sequence_type,
                "acquisitionPlane" : sequence.acquisition_plane,
                "resolution" : sequence.resolution
            }
            
            # Append the sequence object to the project object
            project_info["sequences"].append(sequence_info)

        # Get all segmentations of the project
        segmentations = Segmentation.query.filter_by(project_id = project_id)

        for segmentation in segmentations:
            # Create an object for each segmentation in the project
            segmentation_info = {
                "segmentationID" : segmentation.segmentation_id,
                "t1Sequence" : segmentation.t1_sequence,
                "t1kmSequence" : segmentation.t1km_sequence,
                "t2Sequence" : segmentation.t2_sequence,
                "flairSequence" : segmentation.flair_sequence,
                "model" : segmentation.model,
                "dateTime" : segmentation.date_time,
                "segmentationName" : segmentation.segmentation_name
            }

            # Append the segmentation object to the projhect object
            project_info["segmentations"].append(segmentation_info)

        # Append the project object to the response
        response.append(project_info)

    return response


@main_blueprint.route("/predict", methods=["POST"])
def run_task():
    # Get data from request
    segmentation_data = request.get_json()
    user_id = 1 # TODO: Get this from session cookie
    project_id = segmentation_data["projectID"]
    model = segmentation_data["model"]

    # TODO: Input Validation (e.g., using Pydantic)

    preprocessed_segmentation = db.session.query(Segmentation).filter_by(flair_sequence=segmentation_data["flair"], t1_sequence=segmentation_data["t1"], t1km_sequence=segmentation_data["t1km"], t2_sequence=segmentation_data["t2"]).first()

    # Create new segmentation object
    new_segmentation = Segmentation(
        project_id = project_id,
        segmentation_name = segmentation_data["segmentationName"],
        t1_sequence = segmentation_data["t1"],
        t1km_sequence = segmentation_data["t1km"],
        t2_sequence = segmentation_data["t2"],
        flair_sequence = segmentation_data["flair"],
        model = model,
    )

    print("Auto-created date:", new_segmentation.date_time)

    try:
        # Add new segmentation
        db.session.add(new_segmentation)
        db.session.flush()  # Use flush to get segmentation_id
        
        # Create new directory for the segmentation
        segmentation_id = new_segmentation.segmentation_id
        new_segmentation_path = f'/usr/src/image-repository/{user_id}/{project_id}/segmentations/{segmentation_id}'
        os.makedirs(new_segmentation_path)

        # Get sequence ids and check which need to be preprocessed
        sequence_ids = {      
            "flair": segmentation_data["flair"],  
            "t1": segmentation_data["t1"],
            "t1km": segmentation_data["t1km"],
            "t2": segmentation_data["t2"]
        }

        # Starting Preprocessing and Prediction Task 
        with Connection(redis.from_url("redis://redis:6379/0")):
            q = Queue("my_queue") # Define the queue
            if not preprocessed_segmentation:
                # Preprocessing Task
                task_1 = q.enqueue(
                    preprocessing_task,
                    args=[user_id, project_id, sequence_ids],
                    job_timeout=3600) #60 min  
                # Prediction Task
                task_2 = q.enqueue(
                    prediction_task,
                    depends_on=task_1, 
                    args=[user_id, project_id, segmentation_id, sequence_ids, model],
                    job_timeout=1800) #30 min

                # Update segmentation object and commit to DB
                new_segmentation.preprocessing_id = task_1.get_id()  
                new_segmentation.prediction_id = task_2.get_id()  

                db.session.commit()

                return jsonify({'message': 'Jobs started successfully!', 'preprocessing_id': task_1.id, 'prediction_id': task_2.id, 'segmentation_id': segmentation_id}), 202

            else:
                # If the sequences are already preprocessed, we don't need a preprocessing task
                preprocessing_id = preprocessed_segmentation.preprocessing_id
                preprocessing_job = q.fetch_job(preprocessing_id)

                # If the preprocessing job is not finished, we have to wait for it
                if(preprocessing_job and not preprocessing_job.is_finished):
                    task = q.enqueue(
                        prediction_task, 
                        depends_on=preprocessing_job,
                        args=[user_id, project_id, segmentation_id, sequence_ids, model],
                        job_timeout=1800) # Prediction Task
                else:
                    task = q.enqueue(
                        prediction_task, 
                        args=[user_id, project_id, segmentation_id, sequence_ids, model],
                        job_timeout=1800) 

                # Update segmentation object and commit to DB
                new_segmentation.prediction_id = task.get_id()
                new_segmentation.preprocessing_id = preprocessing_id

                db.session.commit()

                return jsonify({'message': 'Jobs started successfully!', 'preprocessing_id': preprocessing_id, 'prediction_id': task.id, 'segmentation_id': segmentation_id}), 202

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

        # Initialize temp directory for classification
        unique_id = str(uuid.uuid4())
        classifier_path = os.path.join("temp", unique_id)
        os.makedirs(classifier_path)

        # Add all sequences to the database
        for sequence_data in file_infos:
            sequence_name = sequence_data.get('sequence_name')
            sequence_type = sequence_data.get('sequence_type')

            # Create new sequence object
            new_sequence = Sequence(
                project_id=project_id,
                sequence_name=sequence_name,
                sequence_type=sequence_type,
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

            add_to_classification = True

            # Extract dicom files to the correct folder
            with zipfile.ZipFile(files) as z:
                # List all files in the zip archive
                for file in z.namelist():
                    # Check if the file is in the desired sub-folder
                    if file.startswith(sequence_name):
                        filename = os.path.basename(file)
                        dirname = os.path.dirname(file)
                        # skip directories
                        if not filename:
                            continue
                        
                        # Add one slice of each sequence to the temp directory for classification
                        if add_to_classification:
                            os.makedirs(os.path.join(classifier_path, dirname))
                            source = z.open(file)
                            target = open(os.path.join(classifier_path, file), "wb")
                            with source, target:
                                shutil.copyfileobj(source, target)
                            add_to_classification = False

                        # copy file to the correct destination
                        source = z.open(file)
                        target = open(os.path.join(sequence_directory, filename), "wb")
                        with source, target:
                            shutil.copyfileobj(source, target)

        # Run classification
        classification = dicom_classifier.classify(classifier_path)
        shutil.rmtree(classifier_path)

        # Set database entries according to classification
        for seq_type, seq_list in classification.items():
            for seq in seq_list:
                sequence_entry = db.session.query(Sequence).filter_by(sequence_name=seq["path"], project_id=project_id).first()
                if seq_type != "rest":
                    sequence_entry.sequence_type = seq_type
                    sequence_entry.classified_sequence_type = seq_type

                sequence_entry.acquisition_plane = seq["acquisition_plane"]
                sequence_entry.resolution = seq["resolution"]

        # Commit project and sequences to the database
        db.session.commit()

        return jsonify({'message': 'Project and sequences created successfully!', "project_id": project_id, "sequence_ids": sequence_ids}), 201

    except Exception as e:
        print("Error: ", e)
        db.session.rollback()
        return jsonify({'message': f'Error occurred while creating the project: {str(e)}'}), 500
    


@main_blueprint.route("/sequence-types", methods=["PATCH"])
def store_sequence_types():
    try:
        # TODO: Make sure a user can only update his own sequence types

        # Get data from request
        sequence_types = request.get_json()

        # Assign sequence types to database
        for sequence in sequence_types:
            sequence_entry = db.session.query(Sequence).filter_by(sequence_id=sequence["sequence_id"]).first()
            sequence_entry.sequence_type = sequence["sequence_type"]
        
        db.session.commit()

        return jsonify({'message': 'Sequence types sucessfully uploaded!'}), 200
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': f'Error occurred while updating sequence types: {str(e)}'}), 500