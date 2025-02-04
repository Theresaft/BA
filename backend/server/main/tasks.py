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
from server.models import Project, Segmentation, Sequence

# mock flask to create db connection
app = Flask(__name__) 
app.config["SQLALCHEMY_DATABASE_URI"] =  "mysql+pymysql://user:user_password@mysqlDB:3306/my_database"
db.init_app(app)

client = None

try:
    client = docker.DockerClient(base_url='unix://var/run/docker.sock')
    client.ping()
except docker.errors.DockerException as error:
    print(f"Failed to connect to Docker Socket: {error}")

# General preprocessing steps provided by Jan (for all models the same) 
def preprocessing_task(user_id, project_id, segmentation_id, sequence_ids_and_names, user_name, workplace, project_name):
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
    processed_data_path = f'/usr/src/image-repository/{user_id}-{user_name}-{workplace}/{project_id}-{project_name}/preprocessed/{sequence_ids_and_names["flair"][0]}_{sequence_ids_and_names["t1"][0]}_{sequence_ids_and_names["t1km"][0]}_{sequence_ids_and_names["t2"][0]}'

    if os.path.exists(processed_data_path) and os.path.isdir(processed_data_path):
        shutil.rmtree(processed_data_path)

    os.mkdir(processed_data_path)

    # Build the Docker image if it doesnt exist
    image_exists = any("preprocessing:brainns" in image.tags for image in client.images.list())
    if not image_exists:
        print(f"Image preprocessing doesn't exist. Creating image...")
        image, build_logs = client.images.build(path='/usr/src/preprocessing', tag="preprocessing:brainns", rm=True)

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
            for seq in ["flair", "t1", "t1km", "t2"]:
                seq_id = sequence_ids_and_names[seq][0]
                path = os.path.join(raw_data_path, f'{seq_id}/{seq_id}.nii.gz')
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
    
    nifti2dicom.convert_base_image(os.path.join(processed_data_path, "nifti_flair_register.nii.gz"), os.path.join(processed_data_path, "dicom/flair"), os.path.join(raw_data_path, f"{sequence_ids_and_names["flair"][0]}-{sequence_ids_and_names["flair"][1]}"))
    nifti2dicom.convert_base_image(os.path.join(processed_data_path, "nifti_t1_register.nii.gz"), os.path.join(processed_data_path, "dicom/t1"), os.path.join(raw_data_path, f"{sequence_ids_and_names["t1"][0]}-{sequence_ids_and_names["t1"][1]}"))
    nifti2dicom.convert_base_image(os.path.join(processed_data_path, "nifti_t2_register.nii.gz"), os.path.join(processed_data_path, "dicom/t2"), os.path.join(raw_data_path, f"{sequence_ids_and_names["t2"][0]}-{sequence_ids_and_names["t2"][1]}"))
    nifti2dicom.convert_base_image(os.path.join(processed_data_path, "nifti_t1c_register.nii.gz"), os.path.join(processed_data_path, "dicom/t1km"), os.path.join(raw_data_path, f"{sequence_ids_and_names["t1km"][0]}-{sequence_ids_and_names["t1km"][1]}"))

    return True


# Sperate prediction Task for every model
def prediction_task(user_id, project_id, segmentation_id, sequence_ids_and_names, model, user_name, workplace, project_name):
    # TODO: Remove once frontend can handle model selection
    # model = "deepmedic-model:brainns"
    model = "nnunet-model:brainns"

    # Get model specific configuration
    config = model_config(model, segmentation_id)

    # Update the status of the segmentation
    with app.app_context():
        try:
            segmentation = db.session.query(Segmentation).filter_by(segmentation_id=segmentation_id).first()
            if segmentation:
                segmentation.status = "PREDICTING"
                db.session.commit()                    
        except Exception as e:
            print("ERROR: ", e)
    
    # Build the Docker image if it doesnt exist
    image_exists = any(model in image.tags for image in client.images.list())
    if not image_exists:
        print(f"Image ${model} doesn't exist. Creating image...")
        image, build_logs = client.images.build(path=config["docker_file_path"], tag=model, rm=True)

    # This wonderful function waits until a GPU is free
    deviceIDs = GPUtil.getFirstAvailable(order = 'memory', maxLoad=0.5, maxMemory=0.5, attempts=100, interval=5, verbose=False)
    print("Chosen GPU: ", deviceIDs)


    data_path = os.getenv('DATA_PATH') # Das muss einen host-ordner (nicht im container) referenzieren, da es an sub-container weitergegeben wird
    processed_data_path = f'/usr/src/image-repository/{user_id}-{user_name}-{workplace}/{project_id}-{project_name}/preprocessed/{sequence_ids_and_names["flair"][0]}_{sequence_ids_and_names["t1"][0]}_{sequence_ids_and_names["t1km"][0]}_{sequence_ids_and_names["t2"][0]}'
    result_path = f'/usr/src/image-repository/{user_id}-{user_name}-{workplace}/{project_id}-{project_name}/segmentations/{segmentation_id}'
    output_bind_mount_path = f'{data_path}/{user_id}-{user_name}-{workplace}/{project_id}-{project_name}/segmentations/{segmentation_id}'
    print(f"PATHS:\nprocessed_data_path: {processed_data_path}\nresult_path: {result_path}\noutput_bind_mount_path: {output_bind_mount_path}")
    #  Create the container
    container = client.containers.create(
        image = config["image"],
        name = config["container_name"],
        command = config["command"], # This command will be executed inside the spawned nnunet-container
        #command=["tail", "-f", "/dev/null"], # debug command keeps container alive
        volumes = {
            output_bind_mount_path: { 
                'bind': config["output_path"],
                'mode': 'rw',
            },
        },
        device_requests = [
            {
                'Driver': 'nvidia',
                'Capabilities': [['gpu']],
                'DeviceIDs': [str(deviceIDs[0])]  # https://github.com/docker/docker-py/issues/2395
            }
        ],
        detach = True, 
        auto_remove = True
    )

    # Copy t1, t1km, t2, flair in input dir of model container
    tarstream = BytesIO()
    tar = tarfile.TarFile(fileobj=tarstream, mode='w')

    for index,seq in enumerate(["flair", "t1_norm", "t1c", "t2"]):
        path = os.path.join(processed_data_path, f'nifti_{seq}_register.nii.gz')
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
    
    segmentation_path = f'/usr/src/image-repository/{user_id}/{project_id}/segmentations/{segmentation_id}'
    os.mkdir(os.path.join(segmentation_path, "dicom"))
    nifti2dicom.convert_segmentation_to_3d_dicom(os.path.join(segmentation_path, ".nii.gz"), os.path.join(segmentation_path, "dicom/segmentation.dcm"))

    return True


def model_config(model, segmentation_id):
    match model:
        case "nnunet-model:brainns":
            return {
                "image": "nnunet-model:brainns",
                "container_name": f'nnUnet_container_{segmentation_id}',
                "command": ["nnUNet_predict", "-i", "/app/input", "-o", '/app/output', "-t", "1", "-m", "3d_fullres"],
                "output_path" : '/app/output',
                "docker_file_path" : "/usr/src/models/nnUnet"
            }
        case "deepmedic-model:brainns":
            return {
                "image": "deepmedic-model:brainns",
                "container_name": f'deepmedic_container_{segmentation_id}',
                "command": ["./deepMedicRun", 
                  "-model", "./config/model/modelConfig.cfg", 
                  "-test", "./config/test/testConfig.cfg", 
                  "-load", "./model/tinyCnn.trainSessionWithValidTiny.final.2024-11-24.13.12.26.394361.model.ckpt"],
                "output_path" : '/app/output/predictions/prediction_test/predictions',
                "docker_file_path" : "/usr/src/models/deepMedic"
            }
        case _:
            print("The model doesn't exist.")



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