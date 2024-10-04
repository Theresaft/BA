import docker
import os
import shutil
import docker.errors
import GPUtil
import SimpleITK as sitk
from server.database import db
from server.models import Sequence

client = None

try:
    client = docker.DockerClient(base_url='unix://var/run/docker.sock')
    client.ping()
except docker.errors.DockerException as error:
    print(f"Failed to connect to Docker Socket: {error}")

# General preprocessing steps provided by Jan (for all models the same) 
def preprocessing_task(user_id, project_id, sequence_ids):

    raw_data_path = f'/usr/src/image-repository/{user_id}/{project_id}/raw' 
    processed_data_path = f'/usr/src/image-repository/{user_id}/{project_id}/preprocessed'

    for seq in sequence_ids:
        src_path = os.path.join(raw_data_path, str(seq))
        
        # Read DICOM Sequence
        series_reader = sitk.ImageSeriesReader()
        series_filenames = series_reader.GetGDCMSeriesFileNames(src_path)
        series_reader.SetFileNames(series_filenames)
        image_data = series_reader.Execute()

        # Convert DICOM to NIFTI
        nifti_output_path = os.path.join(processed_data_path, f'{seq}.nii.gz')
        sitk.WriteImage(image_data, nifti_output_path)
    
    return True


# Sperate prediction Task for every model
def prediction_task(user_id, project_id, segmentation_id, sequence_ids, model):
    # 1. Model specific preprocessing steps
    # 2. Save Preprocessed Data?
    # 3. Create DB entry for the "ressource" (referencing model specific preprocessed Data)
    # 4. Call model API and wait for result (segmentation)
    
    # TODO: Theoretisch könnte man hier nochmal überprüfen ob das model image noch existiert und zu not neu erstellen. Der Ansatz unten scheint aber noch etwas buggy zu sein und braucht sehr viel Zeit zum überprüfen
    # Note: We are building the image from within the backend/api container. Also the workdirectory of the backend container is set to "app" -> path relativ from there
    # Build the Docker image if it doesnt exist

    # image_exists = any(image_tag in image.tags for image in client.images.list())
    # if not image_exists:
    #     image, build_logs = client.images.build(path='server/main/tasks/nnunet', tag=image_tag) 

    # This wonderful function waits until a GPU is free
    deviceIDs = GPUtil.getFirstAvailable(order = 'memory', maxLoad=0.5, maxMemory=0.5, attempts=100, interval=5, verbose=False)
    print("Chosen GPU: ", deviceIDs)

    data_path = os.getenv('DATA_PATH') # Das muss einen host-ordner (nicht im container) referenzieren, da es an sub-container weitergegeben wird
    input_bind_mount_path = f'{data_path}/{user_id}/{project_id}/preprocessed'
    output_bind_mount_path = f'{data_path}/{user_id}/{project_id}/segmentations/{segmentation_id}'
    

    #  Create and start the container
    client.containers.run(
        image = model,
        name = 'nnUnet_container',
        command = ["nnUNet_predict", "-i", "/app/input", "-o", f'/app/output', "-t", "1", "-m", "3d_fullres"], # This command will be executed inside the spawned nnunet-container
        #command=["tail", "-f", "/dev/null"], # debug command keeps container alive
        volumes = {
            input_bind_mount_path: { # Wir bind mounten hier direkt das HOST Volume
                'bind': '/app/input',
                'mode': 'rw',
            },
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
    
    return True
