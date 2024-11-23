import docker
import os
import docker.errors
import GPUtil
import tarfile
from io import BytesIO
from server.database import db
from flask import Flask
from server.models import Segmentation

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
def preprocessing_task(user_id, project_id, segmentation_id, sequence_ids):
    with app.app_context():
        try:
            # Update the status of the segmentation
            segmentation = db.session.query(Segmentation).filter_by(segmentation_id=segmentation_id).first()
            if segmentation:
                segmentation.status = "PREPROCESSING"
                db.session.commit()                    
        except Exception as e:
            print("ERROR: ", e)

    raw_data_path = f'/usr/src/image-repository/{user_id}/{project_id}/raw' 
    processed_data_path = f'/usr/src/image-repository/{user_id}/{project_id}/preprocessed/{sequence_ids["flair"]}_{sequence_ids["t1"]}_{sequence_ids["t1km"]}_{sequence_ids["t2"]}'

    os.mkdir(processed_data_path)

    # Build the Docker image if it doesnt exist
    image_exists = any("preprocessing:brainns" in image.tags for image in client.images.list())
    if not image_exists:
        print(f"Image preprocessing doesn't exist. Creating image...")
        image, build_logs = client.images.build(path='/usr/src/preprocessing', tag="preprocessing:brainns", rm=True)

    data_path = os.getenv('DATA_PATH') # Das muss einen host-ordner (nicht im container) referenzieren, da es an sub-container weitergegeben wird
    output_bind_mount_path = f'{data_path}/{user_id}/{project_id}/preprocessed/{sequence_ids["flair"]}_{sequence_ids["t1"]}_{sequence_ids["t1km"]}_{sequence_ids["t2"]}'

    # Create the container
    container = client.containers.create(
        image = "preprocessing:brainns",
        name = f'preprocessing_container_{segmentation_id}',
        command = "python main.py -p nifti", # This command will be executed inside the spawned preprocessing-container
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

    for seq in ["flair", "t1", "t1km", "t2"]:
        seq_id = sequence_ids[seq]
        path = os.path.join(raw_data_path, f'{seq_id}/')
        if seq == "t1km":
            tar.add(path, arcname="t1c/")
        else:
            tar.add(path, arcname=f'{seq}/')
        
    
    tar.close()
    tarstream.seek(0)

    success = container.put_archive('/app/input', tarstream)

    if not success:
        raise Exception('Failed to copy input files to preprocessing container')

    # Start the preprocessing container
    container.start()

    # Wait for the container to finish
    container.wait()
    
    return True


# Sperate prediction Task for every model
def prediction_task(user_id, project_id, segmentation_id, sequence_ids, model):

    with app.app_context():
        try:
            # Update the status of the segmentation
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
        image, build_logs = client.images.build(path='/usr/src/models/nnUnet', tag=model, rm=True)

    # This wonderful function waits until a GPU is free
    deviceIDs = GPUtil.getFirstAvailable(order = 'memory', maxLoad=0.5, maxMemory=0.5, attempts=100, interval=5, verbose=False)
    print("Chosen GPU: ", deviceIDs)


    data_path = os.getenv('DATA_PATH') # Das muss einen host-ordner (nicht im container) referenzieren, da es an sub-container weitergegeben wird
    processed_data_path = f'/usr/src/image-repository/{user_id}/{project_id}/preprocessed/{sequence_ids["flair"]}_{sequence_ids["t1"]}_{sequence_ids["t1km"]}_{sequence_ids["t2"]}'
    output_bind_mount_path = f'{data_path}/{user_id}/{project_id}/segmentations/{segmentation_id}'

    #  Create the container
    container = client.containers.create(
        image = model,
        name = f'nnUnet_container_{segmentation_id}',
        command = ["nnUNet_predict", "-i", "/app/input", "-o", f'/app/output', "-t", "1", "-m", "3d_fullres"], # This command will be executed inside the spawned nnunet-container
        # command=["tail", "-f", "/dev/null"], # debug command keeps container alive
        volumes = {
            output_bind_mount_path: { 
                'bind': '/app/output',
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
    container.wait()

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
            segmentation_id = job.meta.get('segmentation_id')

            # Update the status of the segmentation
            segmentation = db.session.query(Segmentation).filter_by(segmentation_id=segmentation_id).first()
            if segmentation:
                segmentation.status = "ERROR"
                db.session.commit()
        except Exception as e:
            print("ERROR: ", e)