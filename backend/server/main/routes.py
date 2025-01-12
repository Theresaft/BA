# server/main/routes.py
from flask import request, jsonify, send_file
import redis
from rq import Queue, Connection
from flask import Blueprint, jsonify, request, g
import uuid
import os
import shutil
from . import dicom_classifier
import zipfile
# Note: Since we are inside a docker container we have to adjust the imports accordingly
from server.database import db
from server.main.tasks import preprocessing_task, prediction_task, report_segmentation_finished, report_segmentation_error 
from server.models import Segmentation, Project, Sequence, Session
import json
from io import BytesIO
from pathlib import Path
from datetime import datetime, timezone


main_blueprint = Blueprint(
    "main",
    __name__,
)

# Middleware
# parses session_token to user_id for all requests
@main_blueprint.before_request
def authenticate_user():
    # skip auth for options
    if request.method == 'OPTIONS':
        return
    
    # todo: add store_sequence_informations
    # do not use middleware for requests, that dont need the user_id
    public_endpoints = ['main.assign_types']
    
    if request.endpoint in public_endpoints:
        return

    # retrieve token from header
    auth_header = request.headers.get('Authorization', '')
    if not auth_header.startswith('Bearer '):
        return jsonify({'message': 'Missing or invalid Authorization header'}), 401

    session_token = auth_header.replace('Bearer ', '').strip()

    # validate token
    session = Session.query.filter_by(session_token=session_token).first()
    if session is None:
        return jsonify({'message': 'Invalid session token'}), 401

    # save user_id for routes to use
    g.user_id = session.user_id

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
@main_blueprint.route("/segmentations/<segmentation_id>/imagedata", methods=["GET"])
def get_segmentation(segmentation_id):
    user_id = g.user_id

    # TODO: Check if Segmentaion belongs to user and exists
    segmentation = Segmentation.query.filter_by(segmentation_id=segmentation_id).first()
   
    # All paths for files to include in the zip
    raw_path = f'/usr/src/image-repository/{user_id}/{segmentation.project_id}/raw'
    t1_path = Path(f'{raw_path}/{segmentation.t1_sequence}')
    t1km_path = Path(f'{raw_path}/{segmentation.t1km_sequence}')
    t2_path = Path(f'{raw_path}/{segmentation.t2_sequence}')
    flair_path = Path(f'{raw_path}/{segmentation.flair_sequence}')
    segmentations_path = Path(f'/usr/src/image-repository/{user_id}/{segmentation.project_id}/segmentations/{segmentation_id}')

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


# This function deletes the project with the given project ID. If the deletion succeeds, 
# TODO: Validate that the user may actually delete the given project ID.
@main_blueprint.route("/projects/<project_id>", methods=["DELETE"])
def delete_project(project_id):
    user_id = g.user_id

    # Also filter by user ID as a security mechanism
    project_to_delete = Project.query.filter_by(user_id = user_id, project_id = project_id)

    try:
        num_rows_before = Project.query.count()
        # TODO Delete all connected sequences and segmentations with the given project ID
        # Register the delete
        project_to_delete.delete()
        # Execute the deletion
        db.session.commit()
        num_rows_after = Project.query.count()

        # We only consider the operation successful if the number of rows is exactly one less than
        # before.
        if num_rows_after != num_rows_before - 1:
            raise Exception(f"No row was deleted from the projects database for project {project_id}!")
    except Exception as e:
        # Undo changes due to error
        print(e)
        db.session.rollback()
        return jsonify({'message': f'Error occurred while trying to delete project {project_id}'}), 500
        
    return jsonify({'message': f'Project {project_id} successfully deleted!'}), 200


# This function deletes the project with the given project ID. If the deletion succeeds, 
# TODO: Validate that the user may actually delete the given project ID.
@main_blueprint.route("/segmentations/<segmentation_id>", methods=["DELETE"])
def delete_segmentation(segmentation_id):
    user_id = g.user_id

    try:
        num_rows_before = Segmentation.query.count()

        # Get all users that belong to the logged in user ID and among those, search for the
        # given segmentation ID. This ensures that nobody can delete someone else's segmentation.
        relevant_segmentation = Segmentation.query.filter_by(segmentation_id = segmentation_id)
        if relevant_segmentation.first():
            project_id_for_user = Project.query.filter_by(user_id = user_id, project_id = relevant_segmentation.first().project_id).all()
            # If the project belongs to the user, delete the given segmentation. If not, ignore the request.
            if len(project_id_for_user) == 1:
                relevant_segmentation.delete()

        # Register the delete
        # own_segmentation.delete()
        # Execute the deletion
        db.session.commit()
        num_rows_after = Segmentation.query.count()

        # We only consider the operation successful if the number of rows is exactly one less than
        # before.
        if num_rows_after != num_rows_before - 1:
            raise Exception(f"No row was deleted from the segmentations database for segmentation {segmentation_id}!")
    except Exception as e:
        # Undo changes due to error
        print(e)
        db.session.rollback()
        return jsonify({'message': f'Error occurred while trying to delete segmentation {segmentation_id}'}), 500
        
    return jsonify({'message': f'Segmentation {segmentation_id} successfully deleted!'}), 200


# Returns all relevant informations on all projects of the user except the actual sequences
@main_blueprint.route("/projects", methods=["GET"])
def get_projects():
    user_id = g.user_id

    # Get all projects from a given user
    projects = Project.query.filter_by(user_id = user_id)

    response = []
    
    for project in projects:
        project_id = project.project_id

        # Create an object for each project
        project_info = {
            "projectID" : project_id,
            "projectName" : project.project_name,
            "fileType" : project.file_format,
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
                "resolution" : sequence.resolution,
                "selected" : sequence.selected
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
                "segmentationName" : segmentation.segmentation_name,
                "status" : segmentation.status
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
    user_id = g.user_id
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
        status = "QUEUEING",
        date_time = datetime.now(timezone.utc)
    )

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
                    args=[user_id, project_id, segmentation_id, sequence_ids],
                    job_timeout=3600, #60 min  
                    on_failure=report_segmentation_error) 
                # Prediction Task
                task_2 = q.enqueue(
                    prediction_task,
                    depends_on=task_1, 
                    args=[user_id, project_id, segmentation_id, sequence_ids, model],
                    job_timeout=1800, #30 min
                    on_success=report_segmentation_finished,
                    on_failure=report_segmentation_error) 
                
                task_2.meta['segmentation_id'] = segmentation_id  
                task_2.save_meta()

                # Update segmentation object and commit to DB
                new_segmentation.preprocessing_id = task_1.get_id()  
                new_segmentation.prediction_id = task_2.get_id()  

                db.session.commit()

            else:
                # If the sequences are already preprocessed, we don't need a preprocessing task
                preprocessing_id = preprocessed_segmentation.preprocessing_id
                preprocessing_job = q.fetch_job(preprocessing_id)

                # If the preprocessing job is not finished, we have to wait for it
                if(preprocessing_job and not preprocessing_job.is_finished):
                    new_segmentation.status = "PREPROCESSING"

                    task = q.enqueue(
                        prediction_task, 
                        depends_on=preprocessing_job,
                        args=[user_id, project_id, segmentation_id, sequence_ids, model],
                        job_timeout=1800,
                        on_success=report_segmentation_finished,
                        on_failure=report_segmentation_error) 
                
                    task.meta['segmentation_id'] = segmentation_id  
                    task.save_meta()

                else:
                    task = q.enqueue(
                        prediction_task, 
                        args=[user_id, project_id, segmentation_id, sequence_ids, model],
                        job_timeout=1800,
                        on_success=report_segmentation_finished,
                        on_failure=report_segmentation_error) 
                
                    task.meta['segmentation_id'] = segmentation_id  
                    task.save_meta()
                        

                # Update segmentation object and commit to DB
                new_segmentation.prediction_id = task.get_id()
                new_segmentation.preprocessing_id = preprocessing_id

                db.session.commit()

        return jsonify({
            'message': 'Jobs started successfully!',
            'segmentation_data' : {
                'segmentation_id': new_segmentation.segmentation_id,
                'segmentation_name': new_segmentation.segmentation_name,
                "date_time" : new_segmentation.date_time,
                "model" : new_segmentation.model,
                "selected_sequences": {
                    "t1_sequence" : new_segmentation.t1_sequence,
                    "t1km_sequence" : new_segmentation.t1km_sequence,
                    "t2_sequence" : new_segmentation.t2_sequence,
                    "flair_sequence" : new_segmentation.flair_sequence
                },
                "status" : new_segmentation.status
            }
        }), 202
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': f'Error occurred while creating starting prediction: {str(e)}'}), 500


@main_blueprint.route("/segmentation/<segmentation_id>/status", methods=["GET"])
def get_segmentation_status(segmentation_id):
    try:
        # TODO: Users should only have access to their own segmentations
        segmentation = db.session.query(Segmentation).filter_by(segmentation_id=segmentation_id).first()
        if segmentation.status:
            return jsonify({"status": segmentation.status})   
        return jsonify({"status": "ERROR"})
    
    except Exception as e:
        print("ERROR: ", e)
        return jsonify({"status": "ERROR"})


@main_blueprint.route("/projects", methods=["POST"])
def create_project():
    stringified_project_information = request.form.get("project_information")
    print(request.form)
    project_information = json.loads(stringified_project_information)
    file_infos = project_information["file_infos"]
    file_format = project_information["file_format"]
    files = request.files["data"]
    user_id = g.user_id

    # TODO: All kinds of Validations


    if not (file_format == "dicom" or file_format == "nifti"):
        return jsonify({'message': f'Unsupported file format. Supported file formats are dicom or nifti.'}), 400

    # Create new project object
    new_project = Project(
        user_id=user_id,
        project_name=project_information["project_name"],
        file_format=file_format
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
        if file_format == "dicom":
            unique_id = str(uuid.uuid4())
            classifier_path = os.path.join("temp", unique_id)
            os.makedirs(classifier_path)

        # Add all sequences to the database
        for sequence_data in file_infos:
            sequence_name = sequence_data.get('sequence_name')
            sequence_type = sequence_data.get('sequence_type')
            selected = sequence_data.get('selected')

            # Create new sequence object
            new_sequence = Sequence(
                project_id=project_id,
                sequence_name=sequence_name,
                sequence_type=sequence_type,
                selected=selected
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

            match file_format:
                case "dicom":
                    # Extract dicom files to the correct folder
                    with zipfile.ZipFile(files) as z:
                        # Get the files from the sequence
                        relevant_files = [f for f in z.namelist() if f.startswith(sequence_name) and os.path.basename(f)]
                        if not relevant_files:
                            continue
                        
                        # Extract one slice of each sequence to the classifier folder
                        z.extract(relevant_files[0], classifier_path)

                        for file in relevant_files:
                            filename = os.path.basename(file)
                                
                            # Extract each file to the image-repository
                            source = z.open(file)
                            target = open(os.path.join(sequence_directory, filename), "wb")
                            with source, target:
                                shutil.copyfileobj(source, target)
                
                case "nifti":
                    with zipfile.ZipFile(files) as z:
                        # Find the correct nifti file in the zip for each sequence
                        if sequence_name in z.namelist() and (sequence_name.endswith(".nii") or (sequence_name.endswith(".nii.gz"))):
                            source = z.open(sequence_name)
                            target = open(os.path.join(sequence_directory, f"{sequence_id}.nii.gz"), "wb")
                        else:
                            return jsonify({'message': f'Image data for sequence: {sequence_name} is missing.'}), 400

                        # Extract each file to the image-repository
                        with source, target:
                            shutil.copyfileobj(source, target)

        if file_format == "dicom":
            # Run classification
            classification = dicom_classifier.classify(classifier_path)
            shutil.rmtree(classifier_path)

            # Set database entries according to classification
            for seq_type, seq_list in classification.items():
                for seq in seq_list:
                    sequence_entry = db.session.query(Sequence).filter_by(sequence_name=seq["path"], project_id=project_id).first()
                    if seq_type != "rest":
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
    


@main_blueprint.route("/sequences", methods=["PATCH"])
def store_sequence_informations():
    try:
        user_id = g.user_id

        # Get data from request
        sequences = request.get_json()

        # Assign sequence informations to database
        for sequence in sequences:
            sequence_entry = db.session.query(Sequence).filter_by(sequence_id=sequence["sequence_id"]).first()
            sequence_project = db.session.query(Project).filter_by(project_id=sequence_entry.project_id).first()
            if(sequence_project.user_id != user_id):
                return jsonify({'message': f'Access to sequence {sequence_entry.sequence_name} with id {sequence_entry.sequence_id} denied, because it belongs to another user'}), 403
            sequence_entry.sequence_type = sequence["sequence_type"]
            sequence_entry.selected = sequence["selected"]
        
        db.session.commit()

        return jsonify({'message': 'Sequence informations sucessfully uploaded!'}), 200 
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': f'Error occurred while updating sequence informations: {str(e)}'}), 500