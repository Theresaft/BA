from pathlib import Path

import docker
import os
import shutil
import docker.errors
import GPUtil
import tarfile
import server.main.nifti2dicom as nifti2dicom
from io import BytesIO
from server.database import db
from flask import Flask
from server.models import Project, Segmentation, Sequence, DisplayValues
from server.images.helper import zip_preprocessed_files
from server.main.helper import model_config
import os
import pydicom
import numpy as np

import time

# # Determine environment mode ("production" , "development")
mode = os.getenv('ENVIRONMENT', 'development').lower()  # default to development if not set

# Set container user based on environment
container_user = "1050:1050" if mode == "production" else None

# mock flask to create db connection
app = Flask(__name__) 
app.config["SQLALCHEMY_DATABASE_URI"] =  f"mysql+pymysql://{os.getenv('MYSQL_USER')}:{os.getenv('MYSQL_PASSWORD')}@mysqlDB:3306/{os.getenv('MYSQL_DATABASE')}"
db.init_app(app)

client = None
possible_container_prefixes_for_segmentation = ["nnUnet_container_", "deepmedic_container_", "preprocessing_container_"]

try:
    client = docker.DockerClient(base_url='unix://var/run/docker.sock')
    client.ping()
except docker.errors.DockerException as error:
    print(f"Failed to connect to Docker Socket: {error}")

# General preprocessing steps provided by Jan (for all models the same) 
def preprocessing_task(user_id, project_id, segmentation_id, sequence_ids_and_names, user_name, workplace, project_name, skip):
    # Update the status of the segmentation
    with app.app_context():
        try:
            segmentation = db.session.query(Segmentation).filter_by(segmentation_id=segmentation_id).first()
            if segmentation:
                segmentation.status = "PREPROCESSING"
                db.session.commit()
        except Exception as e:
            print("ERROR: ", e)

    raw_data_path = f'/usr/src/image-repository/{user_id}-{user_name}-{workplace}/{project_id}-{project_name}/raw'
    processed_data_path = (
        f'/usr/src/image-repository/{user_id}-{user_name}-{workplace}/'
        f'{project_id}-{project_name}/preprocessed/'
        f'{sequence_ids_and_names.get("flair", ("0",))[0]}_'
        f'{sequence_ids_and_names.get("t1", ("0",))[0]}_'
        f'{sequence_ids_and_names.get("t1km", ("0",))[0]}_'
        f'{sequence_ids_and_names.get("t2", ("0",))[0]}'
    )

    if os.path.exists(processed_data_path) and os.path.isdir(processed_data_path):
        shutil.rmtree(processed_data_path)

    os.mkdir(processed_data_path)

    # Skip preprocessing means moving the file just into the processed file
    if skip:
        for seq in sequence_ids_and_names:
            seq_id = sequence_ids_and_names[seq][0]
            seq_name = sequence_ids_and_names[seq][1]
            rawPath = os.path.join(raw_data_path, f'{seq_id}-{seq_name}/{seq_id}.nii.gz')
            shutil.copy(rawPath, processed_data_path)
            shutil.move(os.path.join(processed_data_path, f'{seq_id}.nii.gz'),
                    os.path.join(processed_data_path, f'{seq}.nii.gz'))

    else:
        # Build the Docker image if it doesnt exist
        image_exists = any("preprocessing:brainns" in image.tags for image in client.images.list())
        if not image_exists:
            print(f"Image preprocessing doesn't exist. Creating image...")
            image, build_logs = client.images.build(path='/usr/src/preprocessing', tag="preprocessing:brainns")
            print("Done creating image!")

        data_path = os.getenv('DATA_PATH') # Das muss einen host-ordner (nicht im container) referenzieren, da es an sub-container weitergegeben wird
        output_bind_mount_path = f'{data_path}/{user_id}-{user_name}-{workplace}/{project_id}-{project_name}/preprocessed/{sequence_ids_and_names["flair"][0]}_{sequence_ids_and_names["t1"][0]}_{sequence_ids_and_names["t1km"][0]}_{sequence_ids_and_names["t2"][0]}'

        with app.app_context():
            project_entry = db.session.query(Project).filter_by(project_id=project_id).first()
            file_format = project_entry.file_format

        # Create the container
        container = client.containers.create(
            image = "preprocessing:brainns",
            name = f'preprocessing_container_{segmentation_id}',
            command = f"python main.py -p nifti -f {file_format}", # This command will be executed inside the spawned preprocessing-container
            # command=["tail", "-f", "/dev/null"], # debug command keeps container alive
            volumes = {
                output_bind_mount_path: {
                    'bind': '/app/output/nifti',
                    'mode': 'rw',
                },
            },
            user=container_user,
            detach = True,
            auto_remove = True
        )

        # Copy raw data in input dir of model container
        tarstream = BytesIO()
        tar = tarfile.TarFile(fileobj=tarstream, mode='w')

        match file_format:
            case "dicom":
                for seq in ["flair", "t1", "t1km", "t2"]:
                    seq_id = sequence_ids_and_names[seq][0]

                    path = os.path.join(raw_data_path, f'{seq_id}-{sequence_ids_and_names[seq][1]}/')
                    if seq == "t1km":
                        tar.add(path, arcname="t1c/")
                    else:
                        tar.add(path, arcname=f'{seq}/')

                tar.close()
                tarstream.seek(0)

                success = container.put_archive('/app/input/dicom', tarstream)

            # TODO: update folderstructure
            case "nifti":
                for seq in ["t1", "t2"]:
                    seq_id = sequence_ids_and_names[seq][0]
                    seq_name = sequence_ids_and_names[seq][1]
                    path = os.path.join(raw_data_path, f'{seq_id}-{seq_name}/{seq_id}.nii.gz')
                    if seq == "t1km":
                        tar.add(path, arcname="nifti_t1c.nii.gz")
                    else:
                        tar.add(path, arcname=f'nifti_{seq}.nii.gz')

                tar.close()
                tarstream.seek(0)

                success = container.put_archive('/app/input/nifti', tarstream)

        if not success:
            raise Exception('Failed to copy input files to preprocessing container')

        # Start the preprocessing container
        container.start()

        # Open a file to store logs
        with open(os.path.join(processed_data_path, "container_logs.log"), "w") as logfile:
            for line in container.logs(stream=True):  # Stream logs from the container
                logfile.write(line.decode("utf-8"))
                logfile.flush()  # Ensure logs are written immediately

        # Wait for the container to finish
        container.wait()

        os.mkdir(os.path.join(processed_data_path, "dicom"))

        # Convert each base image to a single 3d dicom
        # nifti2dicom.convert_base_image_to_3d_dicom(os.path.join(processed_data_path, "nifti_flair_register.nii.gz"), os.path.join(processed_data_path, "dicom/flair"), os.path.join(raw_data_path, f"{sequence_ids_and_names["flair"][0]}-{sequence_ids_and_names["flair"][1]}"))
        # nifti2dicom.convert_base_image_to_3d_dicom(os.path.join(processed_data_path, "nifti_t1_register.nii.gz"), os.path.join(processed_data_path, "dicom/t1"), os.path.join(raw_data_path, f"{sequence_ids_and_names["t1"][0]}-{sequence_ids_and_names["t1"][1]}"))
        # nifti2dicom.convert_base_image_to_3d_dicom(os.path.join(processed_data_path, "nifti_t2_register.nii.gz"), os.path.join(processed_data_path, "dicom/t2"), os.path.join(raw_data_path, f"{sequence_ids_and_names["t2"][0]}-{sequence_ids_and_names["t2"][1]}"))
        # nifti2dicom.convert_base_image_to_3d_dicom(os.path.join(processed_data_path, "nifti_t1c_register.nii.gz"), os.path.join(processed_data_path, "dicom/t1km"), os.path.join(raw_data_path, f"{sequence_ids_and_names["t1km"][0]}-{sequence_ids_and_names["t1km"][1]}"))

        # Convert each base image to a dicom sequence, keep the headers of the original sequences if the original sequences were dicom files
        match file_format:
            case "dicom":
                nifti2dicom.convert_base_image_to_dicom_sequence(os.path.join(processed_data_path, "nifti_flair_register.nii.gz"), os.path.join(processed_data_path, "dicom/flair"), os.path.join(raw_data_path, f"{sequence_ids_and_names["flair"][0]}-{sequence_ids_and_names["flair"][1]}"))
                nifti2dicom.convert_base_image_to_dicom_sequence(os.path.join(processed_data_path, "nifti_t1_register.nii.gz"), os.path.join(processed_data_path, "dicom/t1"), os.path.join(raw_data_path, f"{sequence_ids_and_names["t1"][0]}-{sequence_ids_and_names["t1"][1]}"))
                nifti2dicom.convert_base_image_to_dicom_sequence(os.path.join(processed_data_path, "nifti_t2_register.nii.gz"), os.path.join(processed_data_path, "dicom/t2"), os.path.join(raw_data_path, f"{sequence_ids_and_names["t2"][0]}-{sequence_ids_and_names["t2"][1]}"))
                nifti2dicom.convert_base_image_to_dicom_sequence(os.path.join(processed_data_path, "nifti_t1c_register.nii.gz"), os.path.join(processed_data_path, "dicom/t1km"), os.path.join(raw_data_path, f"{sequence_ids_and_names["t1km"][0]}-{sequence_ids_and_names["t1km"][1]}"))
            case "nifti":
                nifti2dicom.convert_base_image_to_dicom_sequence(os.path.join(processed_data_path, "nifti_flair_register.nii.gz"), os.path.join(processed_data_path, "dicom/flair"))
                nifti2dicom.convert_base_image_to_dicom_sequence(os.path.join(processed_data_path, "nifti_t1_register.nii.gz"), os.path.join(processed_data_path, "dicom/t1"))
                nifti2dicom.convert_base_image_to_dicom_sequence(os.path.join(processed_data_path, "nifti_t2_register.nii.gz"), os.path.join(processed_data_path, "dicom/t2"))
                nifti2dicom.convert_base_image_to_dicom_sequence(os.path.join(processed_data_path, "nifti_t1c_register.nii.gz"), os.path.join(processed_data_path, "dicom/t1km"))


        # Save min and max pixel values of the preprocessed sequence in DB and min and max values based on dicom tags.
        # This can be used to set the window leveling in the viewer
        save_min_max_values(processed_data_path, segmentation_id, file_format)

        dicom_path = os.path.join(processed_data_path, "dicom")
        zip = zip_preprocessed_files(dicom_path)
        file_path = os.path.join(dicom_path, 'sequences.zip')

        with open(file_path, 'wb') as f:
            f.write(zip.getvalue())

    return True


def save_min_max_values(processed_data_path, segmentation_id, file_format, sequence_name):
    sequence_path = f"{processed_data_path}/dicom/{sequence_name}"

    min_preprocessed_value, max_preprocessed_value = get_min_max_pixel_values(sequence_path)

    if file_format == "dicom":
        min_value_by_dicom_tag, max_value_by_dicom_tag = get_window_level_bounds_by_dicom_tags(sequence_path)

    with app.app_context():

        segmentation = db.session.query(Segmentation).filter_by(segmentation_id=segmentation_id).first()
        display_values_id = segmentation.display_values
        display_values = db.session.query(DisplayValues).filter_by(display_values_id=display_values_id).first()

        display_values.min_display_value_custom = min_preprocessed_value
        display_values.max_display_value_custom = max_preprocessed_value

        if file_format == "dicom":
            display_values.min_display_value_by_dicom_tag = min_value_by_dicom_tag
            display_values.max_display_value_by_dicom_tag = max_value_by_dicom_tag

        db.session.commit()

def get_min_max_pixel_values(dicom_folder):
    min_pixel_value = float('inf')
    max_pixel_value = float('-inf')
    
    for filename in os.listdir(dicom_folder):
        filepath = os.path.join(dicom_folder, filename)
        if os.path.isfile(filepath) and filename.lower().endswith('.dcm'):
            dicom_data = pydicom.dcmread(filepath)
            pixel_array = dicom_data.pixel_array

            min_pixel_value = min(min_pixel_value, np.min(pixel_array))
            max_pixel_value = max(max_pixel_value, np.max(pixel_array))
    
    return min_pixel_value, max_pixel_value


def get_window_level_bounds_by_dicom_tags(dicom_folder):
    for filename in os.listdir(dicom_folder):
        filepath = os.path.join(dicom_folder, filename)
        if os.path.isfile(filepath) and filename.lower().endswith('.dcm'):
            dicom_data = pydicom.dcmread(filepath)
            
            if 'WindowCenter' in dicom_data and 'WindowWidth' in dicom_data:
                # Handle potential sequences
                window_center = dicom_data.WindowCenter
                window_width = dicom_data.WindowWidth

                # These might be stored as lists
                if isinstance(window_center, pydicom.multival.MultiValue):
                    window_center = window_center[0]
                if isinstance(window_width, pydicom.multival.MultiValue):
                    window_width = window_width[0]

                # Calculate window level bounds
                window_min = window_center - (window_width / 2)
                window_max = window_center + (window_width / 2)
                
                return window_min, window_max
            else:
                raise ValueError(f"DICOM file {filename} is missing Window Center or Window Width tag.")
    
    raise FileNotFoundError("No valid DICOM files found in the folder.")


def remove_containers_for_segmentation(segmentation_id: int, kill_immediately=False) -> bool:
    """For a given segmentation ID, remove the container(s) with the given segmentation_id, if such a container exists. We should
    be able to assume one container per segmentation ID, but handle the case where several have the gien segmentation ID anyway.
    kill_immediately calls stop on the container with the argument timeout=0, leaving no time for cleanup. If a container
    has been removed, return True, else, return False."""
    containers = client.containers.list()
    # First, we match the suffix, i.e., the segmentation_id with the list of Docker containers.
    containers_with_correct_suffix = list(filter(lambda container: container.name.endswith(str(segmentation_id)), containers))
    # It's possible to have other kinds of containers ending in numbers, so we also have to ensure that the prefix matches, i.e., we have either
    # a preprocessing or prediction container.
    containers_to_remove = list(filter(lambda container: any(container.name.startswith(prefix) for prefix in possible_container_prefixes_for_segmentation), 
                                       containers_with_correct_suffix))
    # We're only supposed to have one container per segmentation id, but it can't hurt to assume to have a list.
    # for container in containers_to_remove:
    for container in containers_to_remove:
        # Stop the container. This also removes it automatically due to auto_remove=True.
        if kill_immediately:
            container.stop(timeout=0)
        else:
            container.stop()
    
    return len(containers_to_remove) > 0

def get_device_requests(config, deviceIDs):
    """Depending on whether the model needs a GPU, return that capability or don't."""
    if config["uses_gpu"]:
        return [
            {
                'Driver': 'nvidia',
                'Capabilities': [['gpu']],
                'DeviceIDs': [str(deviceIDs[0])]  # https://github.com/docker/docker-py/issues/2395
            }
        ]
    else:
        return []

# Sperate prediction Task for every model
def prediction_task(user_id, project_id, segmentation_id, sequence_ids_and_names, model, user_name, workplace, project_name):
    # Get model-specific configuration. May raise an exception if the given model doesn't exist.
    config = model_config(model, segmentation_id)
    segmentation_name = ""
    print("Config:", config)

    # Update the status of the segmentation
    with app.app_context():
        try:
            segmentation = db.session.query(Segmentation).filter_by(segmentation_id=segmentation_id).first()
            if segmentation:
                segmentation.status = "PREDICTING"
                segmentation_name = segmentation.segmentation_name
                db.session.commit()                    
        except Exception as e:
            print("ERROR: ", e)
    
    # Build the Docker image if it doesnt exist
    image_exists = any(model in image.tags for image in client.images.list())
    if not image_exists:
        print(f"Image ${model} doesn't exist. Creating image...")
        image, build_logs = client.images.build(path=config["docker_file_path"], tag=model, rm=True)
        print("Done creating image!")

    # This wonderful function waits until a GPU is free
    deviceIDs = GPUtil.getFirstAvailable(order = 'memory', maxLoad=0.5, maxMemory=0.5, attempts=100, interval=5, verbose=False)
    print("Chosen GPU: ", deviceIDs)

    data_path = os.getenv('DATA_PATH') # Das muss einen host-ordner (nicht im container) referenzieren, da es an sub-container weitergegeben wird
    processed_data_path = (
        f'/usr/src/image-repository/{user_id}-{user_name}-{workplace}/'
        f'{project_id}-{project_name}/preprocessed/'
        f'{sequence_ids_and_names.get("flair", ("0",))[0]}_'
        f'{sequence_ids_and_names.get("t1", ("0",))[0]}_'
        f'{sequence_ids_and_names.get("t1km", ("0",))[0]}_'
        f'{sequence_ids_and_names.get("t2", ("0",))[0]}'
    )
    result_path = f'/usr/src/image-repository/{user_id}-{user_name}-{workplace}/{project_id}-{project_name}/segmentations/{segmentation_id}-{segmentation_name}'
    output_bind_mount_path = f'{data_path}/{user_id}-{user_name}-{workplace}/{project_id}-{project_name}/segmentations/{segmentation_id}-{segmentation_name}'
    print(f"PATHS:\nprocessed_data_path: {processed_data_path}\nresult_path: {result_path}\noutput_bind_mount_path: {output_bind_mount_path}")
    #  Create the container
    container = client.containers.create(
        image = config["image"],
        name = config["container_name"],
        command = config["command"], # This command will be executed inside the spawned container
        # command=["tail", "-f", "/dev/null"], # debug command keeps container alive
        volumes = {
            output_bind_mount_path: { 
                'bind': config["output_path"],
                'mode': 'rw',
            },
        },
        device_requests = get_device_requests(config, deviceIDs),
        user=container_user,
        detach = True,
        auto_remove = True
    )

    # Copy t1, t1km, t2, flair in input dir of model container
    tarstream = BytesIO()
    tar = tarfile.TarFile(fileobj=tarstream, mode='w')

    for index, seq_name in enumerate(sequence_ids_and_names):
        path = os.path.join(processed_data_path, f'{seq_name}.nii.gz')
        tar.add(path, arcname=f'_000{index}.nii.gz')
    
    tar.close()
    tarstream.seek(0)

    success = container.put_archive('/app/input', tarstream)

    if not success:
        raise Exception('Failed to copy input files to model container')

    # Start the model container
    container.start()

    # Open a file to store logs
    with open(os.path.join(result_path, "container_logs.log"), "w") as logfile:
        for line in container.logs(stream=True):  # Stream logs from the container
            logfile.write(line.decode("utf-8"))
            logfile.flush()  # Ensure logs are written immediately
    
    container.wait()
    
    segmentation_path = f'/usr/src/image-repository/{user_id}-{user_name}-{workplace}/{project_id}-{project_name}/segmentations/{segmentation_id}-{segmentation_name}'

    # If there is no output file, we can assume there has been an error
    segmentation_file = None
    for root, _, files in os.walk(segmentation_path):
        for file in files:
            if file.endswith(".nii.gz"):
                segmentation_file = Path(segmentation_path, file)
                # We already found one file. Don't need to go down to subdirs
                break
        # Don't go into the subdirs
        break
    if segmentation_file is None:
        log_path = os.path.join(result_path, "container_logs.log")
        raise Exception(f"The container {container.name} terminated with an error. Please check the log file {log_path} for more information.")

    if config["resampledDataExists"]:
        print("Theresa: ResampledDataExists")
        # If resampled data exists, we have to put it into as preprocessing file for the later viewer
        # Currently, no preprocessing will be started

        #ursprünglich
        #os.rmdir(os.path.join(segmentation_path, "dicom"))
        #os.mkdir(os.path.join(segmentation_path, "dicom"))

        #test
        dicom_dir = os.path.join(segmentation_path, "dicom")
        if os.path.exists(dicom_dir):
            shutil.rmtree(dicom_dir)
        os.mkdir(dicom_dir)


        nifti2dicom.convert_segmentation_to_3d_dicom(segmentation_file, os.path.join(segmentation_path, "dicom/segmentation.dcm"))

        os.mkdir(os.path.join(processed_data_path, "dicom"))

        # Convert each base image to a dicom sequence, keep the headers of the original sequences if the original sequences were dicom files
        nifti2dicom.convert_base_image_to_dicom_sequence(
        os.path.join(result_path, "resampled/_0000_resampled.nii.gz"),
        os.path.join(processed_data_path, "dicom/t2"))

        # Save min and max pixel values of the preprocessed sequence in DB and min and max values based on dicom tags.
        # This can be used to set the window leveling in the viewer
        for _, seq_name in enumerate(sequence_ids_and_names):
            save_min_max_values(processed_data_path, segmentation_id, "nifti", seq_name)

        dicom_path = os.path.join(processed_data_path, "dicom")
        zip = zip_preprocessed_files(dicom_path)
        file_path = os.path.join(dicom_path, 'sequences.zip')

        with open(file_path, 'wb') as f:
            f.write(zip.getvalue())

    return True

############################################
############### Callbacks ##################
############################################

def report_segmentation_finished(job, connection, result, *args, **kwargs):
    with app.app_context():
        try:
            segmentation_id = job.meta.get('segmentation_id')

            # Update the status of the segmentation
            segmentation = db.session.query(Segmentation).filter_by(segmentation_id=segmentation_id).first()
            if segmentation:
                segmentation.status = "DONE"
                db.session.commit()                    
        except Exception as e:
            print("ERROR: ", e)


def report_segmentation_error(job, connection, result, *args, **kwargs):
    with app.app_context():
        try:
            job.refresh()
            segmentation_id = job.meta.get('segmentation_id')

            # Update the status of the segmentation
            segmentation = db.session.query(Segmentation).filter_by(segmentation_id=segmentation_id).first()
            if segmentation:
                segmentation.status = "ERROR"
                db.session.commit()
        except Exception as e:
            print("ERROR: ", e)