# server/main/routes.py
import redis
from rq import Queue, Connection
from flask import Blueprint, jsonify, request, g
import uuid
import os
import shutil
from . import helper
from . import dicom_classifier, tasks
import zipfile
# Note: Since we are inside a docker container we have to adjust the imports accordingly
from server.database import db
from server.main.tasks import preprocessing_task, prediction_task, report_segmentation_finished, report_segmentation_error 
from server.models import Segmentation, Project, Sequence, Session, User, UserSettings, DisplayValues
import json
from pathlib import Path
from datetime import datetime, timezone
from sqlalchemy import select, and_
import time
import re
import gzip

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
    public_endpoints = ['main.assign_types' , "main.get_nifti"]
    
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


@main_blueprint.route("/settings", methods=["GET"])
def get_settings():
    user_id = g.user_id

    try:
        # Get all user settings from a given user
        settings_entries = UserSettings.query.filter_by(user_id = user_id)

        if len(settings_entries.all()) == 1:
            settings = settings_entries.first()

            # Create JSON object from the requested columns
            response = {
                "confirmDeleteEntry" : settings.confirm_delete_entry,
                "numberDisplayedRecentSegmentations" : settings.number_displayed_recent_segmentations,
                "defaultDownloadType" : settings.default_download_type,
                "minMaxWindowLeveling" : settings.min_max_window_leveling
            }

            return jsonify(response), 200

        else:
            raise Exception(f"No matching user settings found for user id {user_id}!")
    except Exception as e:
        # Undo changes due to error
        print(e)
        db.session.rollback()
        return jsonify({'message': f'Error occurred while trying to fetch user settings!'}), 500


@main_blueprint.route("/settings", methods=["POST"])
def update_settings():
    user_id = g.user_id

    try:
        db_settings = UserSettings.query.filter_by(user_id = user_id)
        if len(db_settings.all()) == 1:
            db_setting = db_settings.first()

            new_settings = request.get_json()
            print(new_settings)

            if new_settings["confirmDeleteEntry"] in [True, False] and \
                        bool(re.fullmatch(r"^([1-9]\d*)$", new_settings["numberDisplayedRecentSegmentations"])):
                
                db_setting.confirm_delete_entry = new_settings["confirmDeleteEntry"]
                db_setting.number_displayed_recent_segmentations = new_settings["numberDisplayedRecentSegmentations"]
                db_setting.default_download_type = new_settings["defaultDownloadType"]
                db_setting.min_max_window_leveling = new_settings["minMaxWindowLeveling"]

                db.session.commit()
            else:
                raise Exception(f"Invalid input format!")
        else:
            raise Exception(f"No user settings found for the current user {user_id}!")

        return jsonify({'message': f'Upading settings successful!'}), 200
    except Exception as e:
        # Undo changes due to error
        print(e)
        db.session.rollback()
        return jsonify({'message': f'Error occurred while trying to update settings!'}), 500


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


def get_project_path(user_id, project_id) -> str | None:
    """Given a user ID and a project ID, try to find the corresponding project folder in the image repository.
    If such a folder doesn't exist, return None."""
    image_repository_path = Path("/usr/src/image-repository")
    user_folders = [d for d in image_repository_path.iterdir() if d.is_dir() and d.name.startswith(f"{user_id}-")]
    # If not exactly one user was found, return None
    if len(user_folders) != 1:
        print(f"No matching user {user_id} found!")
        return None
    
    user_path = image_repository_path / user_folders[0].name
    project_folders = [d for d in user_path.iterdir() if d.is_dir() and d.name.startswith(f"{project_id}-")]
    # If not exactly one project was found, return None
    if len(project_folders) != 1:
        print(f"No matching project {project_id} found!")
        return None
    
    project_path = user_path / project_folders[0].name
    return str(project_path)


def get_segmentation_path(user_id, project_id, segmentation_id) -> str | None:
    project_path: str | None = get_project_path(user_id, project_id)
    if project_path is None:
        return None
    
    segmentation_folders = [d for d in (Path(project_path) / "segmentations").iterdir() if d.is_dir() and d.name.startswith(f"{segmentation_id}-")]
    if len(segmentation_folders) != 1:
        print(f"No matching segmentation {segmentation_id} found!")
        return None
    
    segmentation_path = Path(project_path) / "segmentations" / segmentation_folders[0].name
    return str(segmentation_path)



# This function deletes the project with the given project ID.
@main_blueprint.route("/projects/<project_id>", methods=["DELETE"])
def delete_project(project_id):
    user_id = g.user_id

    try:
        # If this raises a ValueError (i.e., the given project_id is not an integer), we go straight
        # to the exception handling. Checking whether the project ID is actually an integer is critical
        # for security reasons (e.g., SQL injections).
        is_project_id_valid: bool = bool(re.fullmatch(r"^(0|[1-9]\d*)$", project_id))
        if not is_project_id_valid:
            raise ValueError(f"Project ID {project_id} invalid!")
        
        num_rows_before = Project.query.count()

        # Also filter by user ID as a security mechanism
        project_to_delete = Project.query.filter_by(user_id = user_id, project_id = project_id)

        # Only continue if we have exactly one valid entry
        if len(project_to_delete.all()) == 1:
            # --- CONTAINER/QUEUE DELETION
            # Stop the Docker containers for all the segmentations. If any one Docker container can't be stopped, we just
            # keep going without retrying to not make the deletion process too long.
            segmentations_to_stop: list[Segmentation] = Segmentation.query.filter_by(project_id = project_to_delete.first().project_id).all()
            segmentation_ids_to_stop: list[str] = [str(segmentation.segmentation_id) for segmentation in segmentations_to_stop]
            successfully_stopped_segmentation_ids: list[str] = []
            # Like in the DELETE route for a segmentation, we first check if the segmentation can still be found in the queue
            # and if not, we try searching the corresponding container in the container list.
            segmentation_ids_deleted_from_queue: list[str] = []

            # Handle the elements in the queue
            with Connection(redis.from_url("redis://redis:6379/0")):
                q = Queue("my_queue")
                for job in q.jobs:
                    # Check if the job's segmentation ID is one of the IDs to stop
                    if str(job.meta['segmentation_id']) in segmentation_ids_to_stop:
                        q.remove(job.id)
                        segmentation_ids_deleted_from_queue.append(str(job.meta['segmentation_id']))
                        successfully_stopped_segmentation_ids.append(str(job.meta['segmentation_id']))
            
            # Handle the containers
            for segmentation_id in segmentation_ids_to_stop:
                # If the segmentation ID has already been deleted from the queue, we don't have to search for containers.
                if segmentation_id not in segmentation_ids_deleted_from_queue:
                    # Here we kill the container immediately because after deleting a project, consistency doesn't matter and especially
                    # for performance reasons.
                    deletion_success = tasks.remove_containers_for_segmentation(segmentation_id, kill_immediately=True)
                    if deletion_success:
                        successfully_stopped_segmentation_ids.append(segmentation_id)

            # Now after a timeout, try deleting all segmentation IDs again that haven't been deleted yet. This is for the special cases that are not in the queue,
            # also were not registered as a Docker container.
            if len(successfully_stopped_segmentation_ids) != len(segmentation_ids_to_stop):
                time.sleep(6)
                for segmentation_id in segmentation_ids_to_stop:
                    if segmentation_id not in successfully_stopped_segmentation_ids:
                        deletion_success = tasks.remove_containers_for_segmentation(segmentation_id, kill_immediately=True)
                        print(f"Container for segmentation ID {segmentation_id} deletion on second attempt {'successful' if deletion_success else 'failed'}!")

            # --- DELETE IMAGE REPOSITORY FOLDERS
            project_path_to_delete: str | None = get_project_path(user_id, project_id)
            if project_path_to_delete is not None:
                print(f"Deleting project {project_path_to_delete} from image-repository...")
                helper.delete_folder(project_path_to_delete)
            
            # --- DB DELETION
            project_to_delete.delete()
            db.session.commit()
            num_rows_after = Project.query.count()

            # We only consider the operation successful if the number of rows is exactly one less than
            # before.
            if num_rows_after != num_rows_before-1:
                raise Exception(f"No row was deleted from the projects database for project {project_id}!")
        else:
            raise Exception("Invalid user ID or project ID!")
    except Exception as e:
        # Undo changes due to error
        print(e)
        db.session.rollback()
        return jsonify({'message': f'Error occurred while trying to delete project {project_id}'}), 500

    return jsonify({'message': f'Project {project_id} successfully deleted!'}), 200


# This function deletes the project with the given project ID. If the deletion succeeds, 
@main_blueprint.route("/segmentations/<segmentation_id>", methods=["DELETE"])
def delete_segmentation(segmentation_id):
    user_id = g.user_id
    project_id = -1
    print("Header:", request.headers)

    try:
        # If this raises a ValueError (i.e., the given segmentation_id is not an integer), we go straight
        # to the exception handling. Checking whether the segmentation ID is actually an integer is critical
        # for security reasons (e.g., SQL injections).
        is_segmentation_id_valid: bool = bool(re.fullmatch(r"^(0|[1-9]\d*)$", segmentation_id))
        if not is_segmentation_id_valid:
            raise Exception("Invalid segmentation ID!")

        num_rows_before = Segmentation.query.count()

        # First of all, get the segmentation in question in the first place to check if it belongs to some user.
        relevant_segmentation = Segmentation.query.filter_by(segmentation_id = segmentation_id)

        # Only continue if we have a valid entry
        if relevant_segmentation.first():
            project_ids_for_user = Project.query.filter_by(user_id = user_id, project_id = relevant_segmentation.first().project_id).all()
            # If the project belongs to the user, delete the given segmentation. If not, ignore the request.
            if len(project_ids_for_user) == 1:
                # --- CONTAINER/QUEUE DELETION
                project_id = project_ids_for_user[0].project_id
                job_deleted_from_queue = False
                # If the segmentation's status is still QUEUEING, remove the element from the queue to ensure it never
                # gets into a later pipeline stage.
                with Connection(redis.from_url("redis://redis:6379/0")):
                    q = Queue("my_queue")
                    for job in q.jobs:
                        print("Job ID:", job.id, "Job's segmentation ID:", job.meta["segmentation_id"], "segmentation ID to remove:", segmentation_id)
                        if str(job.meta['segmentation_id']) == str(segmentation_id):
                            q.remove(job.id)
                            print(f"Job for segmentation {job.meta['segmentation_id']} deleted from queue!")
                            job_deleted_from_queue = True
        
                # Only when the database is clean, we remove the corresponding containers. We don't know if the segmentation with segmentation_id
                # is in the preprocessing or prediction stage, but the tasks module takes care of all that. This is only necessary if we haven't deleted
                # anything from the queue.
                if not job_deleted_from_queue:
                    deletion_success = tasks.remove_containers_for_segmentation(segmentation_id)
                    if not deletion_success:
                        # If no container was deleted, try again in six seconds. It is commonly the case that the Docker container hasn't been created
                        # yet, so we give Docker some time. The number of seconds is the lowest number that seemed to work consistently in the test environment.
                        print(f"Deletion of segmentation container for id {segmentation_id} didn't work the first time. Retrying after a while...")
                        time.sleep(6)
                        deletion_success_second = tasks.remove_containers_for_segmentation(segmentation_id)
                        print(f"Deletion {'successful' if deletion_success_second else 'still not successful'} the second time")
        
                # --- IMAGE REPOSITORY FOLDER DELETION
                segmentation_path_to_delete: str | None = get_segmentation_path(str(user_id), str(project_id), str(segmentation_id))
                if segmentation_path_to_delete is not None:
                    print("Deleting segmentation from image-repository...")
                    helper.delete_folder(segmentation_path_to_delete)
                
                # --- DB DELETION
                relevant_segmentation.delete()
                db.session.commit()
                num_rows_after = Segmentation.query.count()

                # We only consider the operation successful if the number of rows is exactly one less than
                # before. If the DB deletion couldn't be completed, we raise an exception.
                if num_rows_after != num_rows_before-1:
                    raise Exception(f"No row was deleted from the segmentations database for segmentation {segmentation_id}!")
            else: # No matching combination of user ID and segmentation ID
                raise Exception("Invalid user ID or segmentation ID!")
        else: # No matching segmentation ID
            raise Exception("Invalid segmentation ID!")
    
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
                "sizeInBytes": sequence.size_in_bytes,
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
    print("Segmentation data:")
    print(segmentation_data)
    user_id = g.user_id
    project_id = segmentation_data["projectID"]
    model = segmentation_data["model"]
    model_config = helper.model_config(model, "")

    necessarySequences = model_config["necessarySequences"]

    sequence_filters = [
        getattr(Segmentation, f"{seq}_sequence") == segmentation_data[seq]
        for seq in necessarySequences
    ]
    all_filters = [Segmentation.status != "ERROR"] + sequence_filters

    # Get display value entry from existing segmentation with the same sequences or create a new entry
    preprocessed_segmentation = db.session.query(Segmentation).filter(and_(*all_filters)).first()

    display_values = 0
    if preprocessed_segmentation:
        display_values = preprocessed_segmentation.display_values
    else:
        new_display_values = DisplayValues()
        # Add new display_values object
        db.session.add(new_display_values)
        db.session.flush()  # Use flush to get display_values_id
        display_values = new_display_values.display_values_id
    
    # Create new segmentation object
    base_fields = {
        "project_id": project_id,
        "segmentation_name": segmentation_data["segmentationName"],
        "display_values": display_values,
        "model": model,
        "status": "QUEUEING",
        "date_time": datetime.now(timezone.utc),
    }

    # Optional sequence fields – only add them if present in the JSON
    optional_sequences = ["t1", "t1km", "t2", "flair"]
    sequence_fields = {
        f"{key}_sequence": segmentation_data[key]
        for key in optional_sequences
        if key in segmentation_data
    }

    # Combine all fields
    new_segmentation = Segmentation(**base_fields, **sequence_fields)

    try:
        # Add new segmentation
        db.session.add(new_segmentation)
        db.session.flush()  # Use flush to get segmentation_id
        
        # query the user mail from the db
        user = User.query.filter_by(user_id=user_id).first()
        user_mail = user.user_mail if user else "unknown_user"
        
        user_name = helper.get_user_name(user_mail)
        # refers to either uksh or uni luebeck
        domain = helper.get_domain(user_mail)
        
        # query the project name from the db
        project = Project.query.filter_by(project_id=project_id).first()
        project_name = project.project_name if project else "unknown_project"
        
        # Create new directory for the segmentation
        segmentation_id = new_segmentation.segmentation_id
        segmentation_name = new_segmentation.segmentation_name
        new_segmentation_path = f'/usr/src/image-repository/{user_id}-{user_name}-{domain}/{project_id}-{project_name}/segmentations/{segmentation_id}-{segmentation_name}'
        os.makedirs(new_segmentation_path)

        print(f"Predicting segmentation {segmentation_id}")

        # TODO: error handling
        sequence_ids_and_names = {}

        for seq in necessarySequences:
            try:
                seq_id = segmentation_data[seq]
                seq_obj = Sequence.query.filter_by(sequence_id=seq_id).first()
                if seq_obj is None:
                    raise ValueError(f"No sequence found for ID: {seq_id}")
                sequence_ids_and_names[seq] = (seq_id, seq_obj.sequence_name)
            except KeyError:
                raise KeyError(f"Missing key '{seq}' in segmentation_data")

        # Starting Preprocessing and Prediction Task 
        with Connection(redis.from_url("redis://redis:6379/0")):
            q = Queue("my_queue") # Define the queue
            
            # query the user mail from the db
            user = User.query.filter_by(user_id=user_id).first()
            user_mail = user.user_mail if user else "unknown_user"
            user_name = helper.get_user_name(user_mail)
            domain = helper.get_domain(user_mail)
            
            # query the project name from the db
            project = Project.query.filter_by(project_id=project_id).first()
            project_name = project.project_name if project else "unknown_project"

            if not preprocessed_segmentation:
                # Preprocessing Task
                task_1 = q.enqueue(
                    preprocessing_task,
                    args=[user_id, project_id, segmentation_id, sequence_ids_and_names, user_name, domain, project_name, model_config["skipPreprocessing"]],
                    job_timeout=60 * 60, # 60 min
                    on_failure=report_segmentation_error)
                # Prediction Task
                task_2 = q.enqueue(
                    prediction_task,
                    depends_on=task_1, 
                    args=[user_id, project_id, segmentation_id, sequence_ids_and_names, model, user_name, domain, project_name],
                    job_timeout=60 * 60, # 60 min
                    on_success=report_segmentation_finished,
                    on_failure=report_segmentation_error)

                task_1.meta['segmentation_id'] = segmentation_id
                task_1.save_meta()

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
                    # THERESA-TODO Delete Preprocessing before, just for debugging reasons

                    task = q.enqueue(
                        prediction_task,
                        depends_on=preprocessing_job,
                        args=[user_id, project_id, segmentation_id, sequence_ids_and_names, model, user_name, domain, project_name],
                        job_timeout=60 * 60, # 60 min
                        on_success=report_segmentation_finished,
                        on_failure=report_segmentation_error) 
                
                    task.meta['segmentation_id'] = segmentation_id  
                    task.save_meta()

                else:
                    task = q.enqueue(
                        prediction_task, 
                        args=[user_id, project_id, segmentation_id, sequence_ids_and_names, model, user_name, domain, project_name],
                        job_timeout=60 * 60, # 60 min
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
        print(e)
        db.session.rollback()
        return jsonify({'message': f'Error occurred while creating starting prediction: {str(e)}'}), 500


# Get the segmentation status for all segmentations of this user that are either QUEUEING, PREPROCESSING or PREDICTING, i.e.,
# those that are not resolved yet.
@main_blueprint.route("/segmentations/status", methods=["GET"])
def get_all_segmentation_statuses():
    user_id = g.user_id
    # This is a mapping of segmentation IDs to status strings.
    result = {}

    try:
        # Get all the user's projects to check if the segmentations' project ID is in the list of user projects.
        user_projects = Project.query.filter_by(user_id = user_id).all()
        allowed_project_ids = [project.project_id for project in user_projects]
        # Get relevant segmentations, i.e., those of the logged in user.
        user_segmentations = db.session.execute(select(Segmentation).where(Segmentation.project_id.in_(allowed_project_ids))).fetchall()
        # Get row[0] because for some reason, the request above returns 1-element tuples of Segmentations
        result = { row[0].segmentation_id: row[0].status for row in user_segmentations }

        return jsonify(result), 200

    except Exception as e:
        # Undo changes due to error
        print(e)
        db.session.rollback()
        return jsonify({'message': f'Error occurred while trying to fetch segmentation statuses for user {user_id}'}), 500
    


@main_blueprint.route("/projects", methods=["POST"])
def create_project():
    stringified_project_information = request.form.get("project_information")
    print(request.form)
    project_information = json.loads(stringified_project_information)
    file_infos = project_information["file_infos"]
    file_format = project_information["file_format"]
    files = request.files["data"]
    user_id = g.user_id

    print("----- Project information: -----")
    print(project_information)

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

        # query the user mail from the db
        user = User.query.filter_by(user_id=user_id).first()
        user_mail = user.user_mail if user else "unknown_user"
        user_name = helper.get_user_name(user_mail)
        domain = helper.get_domain(user_mail)

        # Create folder structure for project
        project_path = f'/usr/src/image-repository/{user_id}-{user_name}-{domain}/{project_id}-{project_information["project_name"]}'
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
            # remove trailing '/' of sequence_name
            sequence_name = sequence_data.get('sequence_name')
            sequence_type = sequence_data.get('sequence_type')
            size_in_bytes = sequence_data.get('size_in_bytes')
            selected = sequence_data.get('selected')

            # Create new sequence object
            new_sequence = Sequence(
                project_id=project_id,
                sequence_name=sequence_name,
                sequence_type=sequence_type,
                size_in_bytes=size_in_bytes,
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
            # ?
            sequence_directory = os.path.join(f'{raw_directory}/{sequence_id}-{sequence_name}')
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
                        if sequence_name in z.namelist():
                            source = z.open(sequence_name)
                            if sequence_name.endswith(".nii"): 
                                with source, gzip.open(os.path.join(sequence_directory, f"{sequence_id}.nii.gz"), "wb") as target:
                                    shutil.copyfileobj(source, target)
                            elif sequence_name.endswith(".nii.gz"):
                                target = open(os.path.join(sequence_directory, f"{sequence_id}.nii.gz"), "wb")
                                # Extract each file to the image-repository
                                with source, target:
                                    shutil.copyfileobj(source, target)
                        else:
                            return jsonify({'message': f'Image data for sequence: {sequence_name} is missing.'}), 400

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
        # TODO REMOVE Folders in Image Repository so that database and image repository stay synchronized
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
    
@main_blueprint.route("/segmentation/<segmentation_id>/sequences-metadata", methods=["GET"])
def get_meta_data(segmentation_id):
    try:
        user_id = g.user_id
        segmentation = db.session.query(Segmentation).filter_by(segmentation_id=segmentation_id).first()
        project = db.session.query(Project).filter_by(project_id=segmentation.project_id).first()

        if(project.user_id != user_id):
            return jsonify({'message': f'Access to segmentation {segmentation.segmentation_name} with id {segmentation.segmentation_id} denied, because it belongs to another user'}), 403

        display_values = db.session.query(DisplayValues).filter_by(display_values_id=segmentation.display_values).first()

        return jsonify({
            "window-leveling": {
                "t1": {
                    "minMax": {
                        "min" : display_values.t1_min_display_value_custom,
                        "max" : display_values.t1_max_display_value_custom
                    },
                    "dicomTag": {
                        "min" : display_values.t1_min_display_value_by_dicom_tag,
                        "max" : display_values.t1_max_display_value_by_dicom_tag
                    }
                },
                "t1km": {
                    "minMax": {
                        "min" : display_values.t1km_min_display_value_custom,
                        "max" : display_values.t1km_max_display_value_custom
                    },
                    "dicomTag": {
                        "min" : display_values.t1km_min_display_value_by_dicom_tag,
                        "max" : display_values.t1km_max_display_value_by_dicom_tag
                    }
                },
                "t2": {
                    "minMax": {
                        "min" : display_values.t2_min_display_value_custom,
                        "max" : display_values.t2_max_display_value_custom
                    },
                    "dicomTag": {
                        "min" : display_values.t2_min_display_value_by_dicom_tag,
                        "max" : display_values.t2_max_display_value_by_dicom_tag
                    }
                },
                "flair": {
                    "minMax": {
                        "min" : display_values.flair_min_display_value_custom,
                        "max" : display_values.flair_max_display_value_custom
                    },
                    "dicomTag": {
                        "min" : display_values.flair_min_display_value_by_dicom_tag,
                        "max" : display_values.flair_max_display_value_by_dicom_tag
                    }
                },
            },
        }), 200
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': f'Error occurred while retrieving sequence informations: {str(e)}'}), 500