# server/images/routes.py

from flask import request, jsonify, send_file
from flask import Blueprint, jsonify, request, g
import os
import shutil
import zipfile
from . import helper
from server.models import Segmentation, Project, Session, User, Sequence
import json
from io import BytesIO
from pathlib import Path
from server.database import db
import SimpleITK as sitk
from server.main import nifti2dicom
import uuid

images_blueprint = Blueprint(
    "images",
    __name__,
)

# Middleware
# parses session_token to user_id for all requests
@images_blueprint.before_request
def authenticate_user():
    # skip auth for options
    if request.method == 'OPTIONS':
        return
    
    # todo: add store_sequence_informations
    # do not use middleware for requests, that dont need the user_id
    public_endpoints = ['images.get_nifti', 'images.convert_nifti2dicom']
    
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


# This endpoint returns a zip file containing a dicom series of a not preprocessed 
@images_blueprint.route("/sequences/<sequence_id>/imagedata", methods=["GET"])
def get_sequence(sequence_id):
    user_id = g.user_id

    sequence = Sequence.query.filter_by(sequence_id=sequence_id).first()
    project = Project.query.filter_by(project_id=sequence.project_id).first()
    if(project.user_id != user_id):
        return jsonify({'message': f'Access to segmentation {sequence.segmentation_name} with id {sequence.segmentation_id} denied, because it belongs to another user'}), 403
    
    # query the user mail from the db
    user = User.query.filter_by(user_id=user_id).first()
    user_mail = user.user_mail 
    user_name = user_mail.split('@')[0]
    # refers to either uksh or uni luebeck
    domain = helper.get_domain(user_mail)
    # query the project name from the db
    project = Project.query.filter_by(project_id=sequence.project_id).first()
    project_name = project.project_name
    
    # The path to the sequence data
    raw_path = f'/usr/src/image-repository/{user_id}-{user_name}-{domain}/{sequence.project_id}-{project_name}/raw/'
    data_path = os.path.join(raw_path, f'{sequence.sequence_id}-{sequence.sequence_name}/')

    if project.file_format == "nifti":
        dicom_path = os.path.join(raw_path, f"dicom/")
        if not os.path.isdir(dicom_path):
            os.mkdir(dicom_path)
        data_path = os.path.join(dicom_path, f"{sequence.sequence_id}/")
        if not os.path.isdir(data_path):
            nifti_path = os.path.join(raw_path, f"{sequence.sequence_id}-{sequence.sequence_name}/{sequence_id}.nii.gz")
            nifti2dicom.convert_base_image_to_dicom_sequence(nifti_path, data_path)

    zip_file = helper.zip_sequence(data_path)

    # Return the zip file
    response = send_file(
        zip_file,
        mimetype='application/zip',
        download_name='imaging_files.zip',
        as_attachment=True
    )

    return response


# Gets a nifti file, converts it to a dicom series and sends it back in a zip
@images_blueprint.route("/convert/nifti2dicom", methods=["POST"])
def convert_nifti2dicom():
    base_path = "temp"
    unique_id = str(uuid.uuid4())
    unique_path = os.path.join(base_path, unique_id)
    os.mkdir(unique_path)

    # extract the zip files to the unique directory
    nifti_sequence = request.files["nifti_data"]

    with zipfile.ZipFile(nifti_sequence) as z:
        z.extractall(unique_path)

    # get the filename of the given nifti file
    nifti_filename = ""
    for filename in os.listdir(unique_path):
        if filename.endswith(".nii") or filename.endswith(".nii.gz"):
            nifti_filename = filename
            break
    
    if(not nifti_filename):
        return jsonify({"error": "nifti to dicom conversion failed: no nifti file was passed to convert"}), 400

    nifti_path = os.path.join(unique_path, nifti_filename)
    dicom_path = os.path.join(unique_path, "dicom")

    nifti2dicom.convert_base_image_to_dicom_sequence(nifti_path, dicom_path)
    zip_file = helper.zip_sequence(dicom_path)
    shutil.rmtree(unique_path)

    # Return the zip file
    response = send_file(
        zip_file,
        mimetype='application/zip',
        download_name='imaging_files.zip',
        as_attachment=True
    )
    
    return response


# This endpoint returns a zip file containing all preprocessed base images for a segmentation.
# The zip includes four subdirectories (`t1`, `t1km`, `t2`, `flair`), each containing either NIfTI or DICOM files,
@images_blueprint.route("/segmentations/<segmentation_id>/imagedata", methods=["GET"])
def get_segmentation(segmentation_id):
    user_id = g.user_id

    # TODO: Check if Segmentaion belongs to user and exists
    segmentation = Segmentation.query.filter_by(segmentation_id=segmentation_id).first()
   
    # query the user mail from the db
    user = User.query.filter_by(user_id=user_id).first()
    user_mail = user.user_mail 
    user_name = user_mail.split('@')[0]
    # refers to either uksh or uni luebeck
    domain = helper.get_domain(user_mail)
    # query the project name from the db
    project = Project.query.filter_by(project_id=segmentation.project_id).first()
    project_name = project.project_name
    
    # All paths for files to include in the zip
    project_path = f'/usr/src/image-repository/{user_id}-{user_name}-{domain}/{segmentation.project_id}-{project_name}'
    preprocessed_path = (
        f"{project_path}/preprocessed/"
        f"{getattr(segmentation, 'flair_sequence', 0) or 0}_"
        f"{getattr(segmentation, 't1_sequence', 0) or 0}_"
        f"{getattr(segmentation, 't1km_sequence', 0) or 0}_"
        f"{getattr(segmentation, 't2_sequence', 0) or 0}/dicom"
    )

    zip_path = os.path.join(preprocessed_path, "sequences.zip")
    if os.path.isfile(zip_path):
        # Return the zip file
        response = send_file(
            zip_path,
            mimetype='application/zip',
            download_name='imaging_files.zip',
            as_attachment=True
        )
    else:
        zip_file = helper.zip_preprocessed_files(preprocessed_path)
        # Return the zip file
        response = send_file(
            zip_file,
            mimetype='application/zip',
            download_name='imaging_files.zip',
            as_attachment=True
        )

    # Add a header indicating if files are DICOM or NIFTI
    # TODO: Save in DB if Files are DICOM or NIFTI
    response.headers['X-File-Type'] = "DICOM"  # "NIFTI"

    return response

@images_blueprint.route("/segmentations/<segmentation_id>/rawsegmentation", methods=["GET"])
def get_raw_segmentation(segmentation_id):
    user_id = g.user_id

    # TODO: Check if Segmentaion belongs to user and exists
    segmentation = Segmentation.query.filter_by(segmentation_id=segmentation_id).first()
    segmentation_name = segmentation.segmentation_name

    # query the user mail from the db
    user = User.query.filter_by(user_id=user_id).first()
    user_mail = user.user_mail 
    user_name = user_mail.split('@')[0]
    # refers to either uksh or uni luebeck
    domain = helper.get_domain(user_mail)
    # query the project name from the db
    project = Project.query.filter_by(project_id=segmentation.project_id).first()
    project_name = project.project_name
    
    # All paths for files to include in the zip
    project_path = f'/usr/src/image-repository/{user_id}-{user_name}-{domain}/{segmentation.project_id}-{project_name}'

    # Find corresponding nifti file
    segmentations_path = Path(f"{project_path}/segmentations/{segmentation_id}-{segmentation_name}")
    for file in os.listdir(segmentations_path):
        if file.endswith(".nii.gz"):
            nifti_path = Path(segmentations_path) / file
            break

    print(f"Looking for segmentation file at: {nifti_path}")

    # Check if file exists
    if not nifti_path.exists():
        print("Segmentation file not found")
        return jsonify({"error": "Segmentation file not found"}), 404

    # Read the NIfTI file using SimpleITK
    try:
        sitk_image = sitk.ReadImage(str(nifti_path))
        print("NIfTI file successfully read")
    except Exception as e:
        print(f"Error reading NIfTI file: {e}")
        return jsonify({"error": "Error reading NIfTI file"}), 500

    # Convert to NumPy array
    segmentation_array = sitk.GetArrayFromImage(sitk_image)
    print(f"Segmentation array shape: {segmentation_array.shape}, dtype: {segmentation_array.dtype}")

    # Convert NumPy array to list (for JSON serialization)
    segmentation_list = segmentation_array.tolist()
    print("Segmentation successfully converted to list")

    return jsonify({"segmentation": segmentation_list})


@images_blueprint.route("/preprocessed/nifti/test-nifti.nii.gz", methods=["GET"])
def get_nifti():
    # Path to your NIfTI file
    url = "/usr/src/image-repository/1-brainns-uni/1-MyProject/preprocessed/1_14_13_19/nifti_flair_register.nii.gz"
    # Check if the file exists
    if os.path.exists(url):
        # Send the file as a response
        return send_file(url, mimetype='application/gzip', as_attachment=True, download_name="nifti_flair_register.nii.gz")
    else:
        return jsonify({"error": "File not found"}), 404

@images_blueprint.route("/preprocessed/dicom/test-nifti.nii.gz", methods=["GET"])
def get_dicom():
    return "TODO: Implement"

@images_blueprint.route("/download-segmentation/<seg_id>/<file_format>", methods=["GET"])
def download(seg_id, file_format):
    # check if user has access to requested segmentation
    user_id = g.user_id
    segmentation_entry = db.session.query(Segmentation).filter_by(segmentation_id=seg_id).first()
    project_entry = db.session.query(Project).filter_by(project_id=segmentation_entry.project_id).first()

    if(project_entry.user_id != user_id):
        return jsonify({'message': f'Access to segmentation {segmentation_entry.segmentation_name} with id {segmentation_entry.segmentation_id} denied, because it belongs to another user'}), 403

    # Query the user mail from the db
    user = User.query.filter_by(user_id=user_id).first()
    user_mail = user.user_mail 
    user_name = user_mail.split('@')[0]
    # Refers to either uksh or uni luebeck
    domain = helper.get_domain(user_mail)

    # The base paths
    project_path = f'/usr/src/image-repository/{user_id}-{user_name}-{domain}/{project_entry.project_id}-{project_entry.project_name}'
    segmentation_base_path = os.path.join(project_path, f"segmentations/{seg_id}-{segmentation_entry.segmentation_name}")

    # Extract file information from file_format
    if file_format in helper.file_format_mapping:
        relative_path = helper.file_format_mapping[file_format]
    else:
        print(f"invalid fileformat: {file_format}. Only \"nifti\" and \"dicom\" are supported.")
        return jsonify({'message': f"invalid fileformat: {file_format}. Only \"nifti\" and \"dicom\" are supported."})

    segmentation_path = os.path.join(segmentation_base_path, relative_path)
    preprocessed_path = f'{project_path}/preprocessed/{segmentation_entry.flair_sequence}_{segmentation_entry.t1_sequence}_{segmentation_entry.t1km_sequence}_{segmentation_entry.t2_sequence}'

    # Check if the file exists
    if os.path.exists(segmentation_path):
        zip_segmentation = helper.zip_segmentation(segmentation_path=segmentation_path, preprocessed_path=preprocessed_path, file_format=file_format)
        # Send the file as a response
        return send_file(
            zip_segmentation, 
            as_attachment=True, 
            download_name=f"{file_format}_segmentation_{segmentation_entry.segmentation_name}.zip", 
        )
    else:
        return jsonify({"error": "File not found"}), 404