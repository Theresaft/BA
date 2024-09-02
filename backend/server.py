##################################################
                # DEPRECATED #
##################################################
from flask import Flask, request, jsonify, send_file
import os
import SimpleITK as sitk
from flask_cors import CORS
import zipfile
import uuid
import requests
import glob
import server.main.dicom_classifier as dicom_classifier


app = Flask(__name__)
CORS(app)  # Allow CORS for all routes


@app.route('/convert', methods=['POST'])
def convert_dicom_to_nifti():

    # check if all 4 files are provided 
    if not all(key in request.files for key in ['dicom_sequence_1', 'dicom_sequence_2', 'dicom_sequence_3', 'dicom_sequence_4']):  
        return all_in_one()

    dicom_base_path = "dicom-images"
    nifti_base_path = "nifti-images"
    unique_id = str(uuid.uuid4())

    dicom_unique_path = os.path.join(dicom_base_path, unique_id)
    nifti_unique_path = os.path.join(nifti_base_path, unique_id)

    # create unique directories
    os.makedirs(dicom_unique_path)
    os.makedirs(nifti_unique_path)
    
    try:
        # Unzip all four DICOM sequences into the unique directory
        for i in range(1, 5):
            dicom_sequence = request.files[f'dicom_sequence_{i}']
            with zipfile.ZipFile(dicom_sequence) as z:
                z.extractall(dicom_unique_path)

        classification = dicom_classifier.classify("dicom-images")
        if(not (classification[0] and classification[1] and classification[2])):
            return jsonify({"error": f"{'' if classification[0] else 't1,'} {'' if classification[1] else 't2,'} {'' if classification[2] else 'flair'} sequence is missing"}), 400

        # Convert each DICOM sequence to NIFTI
        for subdir in os.listdir(dicom_unique_path):
            dicom_sequence_path = os.path.join(dicom_unique_path, subdir)

            # Read DICOM Sequence
            series_reader = sitk.ImageSeriesReader()
            series_filenames = series_reader.GetGDCMSeriesFileNames(dicom_sequence_path)
            series_reader.SetFileNames(series_filenames)
            image_data = series_reader.Execute()

            # Convert DICOM to NIFTI
            nifti_output_path = os.path.join(nifti_unique_path, f'{subdir}.nii.gz')
            sitk.WriteImage(image_data, nifti_output_path)

        return jsonify({"message": "File converted successfully"}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


def all_in_one():
    dicom_base_path = "dicom-images"
    nifti_base_path = "nifti-images"
    unique_id = str(uuid.uuid4())

    dicom_unique_path = os.path.join(dicom_base_path, unique_id)
    nifti_unique_path = os.path.join(nifti_base_path, unique_id)

    # create unique directories
    os.makedirs(dicom_unique_path)
    os.makedirs(nifti_unique_path)

    dicom_sequence = request.files["dicom_sequence_1"]
    with zipfile.ZipFile(dicom_sequence) as z:
        z.extractall(dicom_unique_path)

    classification = dicom_classifier.classify("dicom-images")

    if(not (classification["t1"] and classification["t1km"] and classification["t2"] and classification["flair"])):
        return jsonify({"error": f"{'' if classification['t1'] else 't1, '} {'' if classification['t1km'] else 't1km, '} {'' if classification['t2'] else 't2, '} {'' if classification['flair'] else 'flair '}sequence is missing"}), 400
    
    best_t1 = dicom_classifier.get_best_resolution(classification["t1"])
    best_t1km = dicom_classifier.get_best_resolution(classification["t1km"])
    best_t2 = dicom_classifier.get_best_resolution(classification["t2"])
    best_flair = dicom_classifier.get_best_resolution(classification["flair"])

    print(best_t1, best_flair, best_t1km, best_t2)

    for path in [best_t1, best_t1km, best_t2, best_flair]:
        series_reader = sitk.ImageSeriesReader()
        series_filenames = series_reader.GetGDCMSeriesFileNames(path)
        series_reader.SetFileNames(series_filenames)
        image_data = series_reader.Execute()

        before, seperator, after = path.rpartition("\\")
        nifti_output_path = os.path.join(nifti_unique_path, f'{after}.nii.gz')
        sitk.WriteImage(image_data, nifti_output_path)

    before, seperator, best_t1 = best_t1.rpartition("\\")
    before, seperator, best_t1km = best_t1km.rpartition("\\")
    before, seperator, best_t2 = best_t2.rpartition("\\")
    before, seperator, best_flair = best_flair.rpartition("\\")
        
    return jsonify({"message": f"Chosen Sequences: T1: {best_t1}, T1KM: {best_t1km}, T2: {best_t2}, Flair: {best_flair}"}), 200


@app.route('/classify', methods=['POST'])
def classify():
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

    # sort the sequences by resolution and extract the relevant data paths
    for type in ["t1", "t1km", "t2", "flair"]:
        classification[type].sort(key = lambda path: dicom_classifier.get_resolution(path))
        classification[type] = [dicom_classifier.get_correct_path(path) for path in classification[type]]

    print(jsonify(classification))

    return jsonify(classification), 200


@app.route('/predict', methods=['POST'])
def predict_mask_nnunet():
    
    # check if all 4 files are provided
    if not all(key in request.files for key in ['dicom_sequence_1', 'dicom_sequence_2', 'dicom_sequence_3', 'dicom_sequence_4']):
        return jsonify({"error": "All 4 DICOM sequences must be provided"}), 400

    try:
        input_dir = '../nnunet-docker/nnunet/input'
        output_dir = '../nnunet-docker/nnunet/output'
        unique_id = str(uuid.uuid4())
        unique_input_path = os.path.join(input_dir, unique_id)
        unique_output_path = os.path.join(output_dir, unique_id)

        # create unique directories
        os.makedirs(unique_input_path)
        os.makedirs(unique_output_path)
        

        # Save all four files in ../nnunet-docker/nnunet/input
        file_paths = []
        for i in range(1, 5):
            file = request.files[f'dicom_sequence_{i}']
            file_path = os.path.join(unique_input_path, file.filename)
            file.save(file_path)
            file_paths.append(file_path)

        # Call the nnunet_predict endpoint
        response = requests.get(f'http://localhost:6000/nnunet_predict/{unique_id}')
        
        if response.status_code != 200:
            return jsonify({"error": "Error occurred during nnUNet prediction"}), response.status_code

        # Retrieve Segmentation Mask
        nii_files = glob.glob(os.path.join(unique_output_path, '*.nii.gz'))
        if not nii_files:
            return jsonify({"error": "Segmentation mask not found"}), 500

        segmentation_mask_path = nii_files[0]

        # Return Segmentation Mask
        return send_file(segmentation_mask_path, mimetype='application/gzip', as_attachment=True, download_name='Segmentation-Mask.nii.gz')

    except Exception as e:
        return jsonify({"error": str(e)}), 500




if __name__ == '__main__':
    app.run(debug=True)

