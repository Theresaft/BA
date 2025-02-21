# server/images/routes.py
from flask import request, jsonify, send_file
from flask import Blueprint, jsonify, request, g
import os
import zipfile
from server.models import Segmentation, Project, Session, User
import json
from io import BytesIO
from pathlib import Path
import SimpleITK as sitk

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
    public_endpoints = ['images.get_nifti']
    
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


# This endpoint returns a zip file containing all images for a segmentation including the raw images.
# The zip includes four subdirectories (`t1`, `t1km`, `t2`, `flair`), each containing either NIfTI or DICOM files,
# and three NIfTI label files (`label_1.nii.gz`, `label_2.nii.gz`, `label_3.nii.gz`) in the root.
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
    workplace = getWorkplace(user_mail.split('@')[1])
    # query the project name from the db
    project = Project.query.filter_by(project_id=segmentation.project_id).first()
    project_name = project.project_name
    
    # All paths for files to include in the zip
    project_path = f'/usr/src/image-repository/{user_id}-{user_name}-{workplace}/{segmentation.project_id}-{project_name}'
    preprocessed_path = f'{project_path}/preprocessed/{segmentation.flair_sequence}_{segmentation.t1_sequence}_{segmentation.t1km_sequence}_{segmentation.t2_sequence}/dicom'
    t1_path = Path(f'{preprocessed_path}/t1')
    t1km_path = Path(f'{preprocessed_path}/t1km')
    t2_path = Path(f'{preprocessed_path}/t2')
    flair_path = Path(f'{preprocessed_path}/flair')
    segmentations_path = Path(f'{project_path}/segmentations/{segmentation_id}')

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

@images_blueprint.route("/segmentations/<segmentation_id>/rawsegmentation", methods=["GET"])
def get_raw_segmentation(segmentation_id):
    user_id = g.user_id

    segmentation_id = 1

    # TODO: Check if Segmentaion belongs to user and exists
    segmentation = Segmentation.query.filter_by(segmentation_id=segmentation_id).first()
   
    # query the user mail from the db
    user = User.query.filter_by(user_id=user_id).first()
    user_mail = user.user_mail 
    user_name = user_mail.split('@')[0]
    # refers to either uksh or uni luebeck
    workplace = getWorkplace(user_mail.split('@')[1])
    # query the project name from the db
    project = Project.query.filter_by(project_id=segmentation.project_id).first()
    project_name = project.project_name
    
    # All paths for files to include in the zip
    project_path = f'/usr/src/image-repository/{user_id}-{user_name}-{workplace}/{segmentation.project_id}-{project_name}'

    segmentations_path = Path(f"{project_path}/segmentations/{segmentation_id}/.nii.gz")


    print(f"Looking for segmentation file at: {segmentations_path}")

    # Check if file exists
    if not segmentations_path.exists():
        print("Segmentation file not found")
        return jsonify({"error": "Segmentation file not found"}), 404

    # Read the NIfTI file using SimpleITK
    try:
        sitk_image = sitk.ReadImage(str(segmentations_path))
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


def getWorkplace(mailDomain):
    if "uni" in mailDomain:
        return "uni"
    elif "uksh" in mailDomain:
        return "uksh"
    return "unknown" 