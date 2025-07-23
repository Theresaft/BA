# Using shutil to remove non empty directories
import shutil

#################################################################################
####  legacy --> deleting from image repository is implemented on routes.py  ####
#################################################################################
# def deleteProjectFromImageRepository(user: User, project: Project):
#     # Build the image-repository path of the project
#     user_name = get_user_name(user.user_mail)
#     domain = get_domain(user.user_mail)
#     path_to_delete = f'/usr/src/image-repository/{user.user_id}-{user_name}-{domain}/{project.project_id}-{project.project_name}'

#     # Delete folder
#     print(f"Deleting project: {path_to_delete} from image repository...")
#     delete_folder(path_to_delete)


# def deleteSegmentationFromImageRepository(user:User, project: Project, seg: Segmentation):
#     # Build the image-repository path of the segmentation
#     user_name = get_user_name(user.user_mail)
#     domain = get_domain(user.user_mail)
#     path_to_delete = f'/usr/src/image-repository/{user.user_id}-{user_name}-{domain}/{project.project_id}-{project.project_name}/segmentations/{seg.segmentation_id}'

#     # Delete folder
#     print(f"Deleting segmentation: {path_to_delete} from image repository...")
#     delete_folder(path_to_delete)

def get_domain(user_mail):
    # Get the domain of mail adress
    mailDomain = user_mail.split('@')[1]

    if "uni" in mailDomain:
        return "uni"
    elif "uksh" in mailDomain:
        return "uksh"
    return "unknown"

def get_user_name(user_mail):
    return user_mail.split("@")[0]

def delete_folder(path_to_delete):
    try:
        shutil.rmtree(path_to_delete)
        print(f"Successfully deleted {path_to_delete} from image repository...")
    except FileNotFoundError:
        print(f"Directory {path_to_delete} not found.")
    except PermissionError:
        print(f"No permission to delete {path_to_delete}.")
    except Exception as e:
        print(f"Failed to delete folder {path_to_delete}: {e}")

def model_config(model, segmentation_id):
    match model:
        case "nnunet-model:brainns":
            return {
                "image": "nnunet-model:brainns",
                "container_name": f'nnUnet_container_{segmentation_id}',
                "command": ["nnUNet_predict", "-i", "/app/input", "-o", '/app/output', "-t", "1", "-m", "3d_fullres"],
                "output_path" : '/app/output',
                "docker_file_path" : "/usr/src/models/nnUnet",
                "uses_gpu": True,
                "necessarySequences": ["t1", "t1-km", "t2", "flair"],
                "skipPreprocessing": False,
                "resampledDataExists": False
            }
        case "own-model:brainns":
            return {
                "image": "own-model:brainns",
                "container_name": f'own_model_container_{segmentation_id}',
                # TODO Don't hard-code these things (like the checkpoint)
                "command": ["python", "src/inference.py",
                            "--lightning-checkpoint=/app/checkpoints/checkpoint-01-04-25-version-server-58-epoch-23.ckpt",
                            "--input-path=/app/input/",
                            "--output-path=/app/output/",
                            "--patch-overlap=24",
                            "--device=cpu"
                            ],
                "output_path" : '/app/output',
                "docker_file_path" : "/usr/src/models/own",
                "uses_gpu": False
            }
        # Not supported yet!
        # case "deepmedic-model:brainns":
        #     return {
        #         "image": "deepmedic-model:brainns",
        #         "container_name": f'deepmedic_container_{segmentation_id}',
        #         "command": ["./deepMedicRun",
        #           "-model", "./config/model/modelConfig.cfg",
        #           "-test", "./config/test/testConfig.cfg",
        #           "-load", "./model/tinyCnn.trainSessionWithValidTiny.final.2024-11-24.13.12.26.394361.model.ckpt"],
        #         "output_path" : '/app/output/predictions/prediction_test/predictions',
        #         "docker_file_path" : "/usr/src/models/deepMedic"
        #     }

    # von Theresa hinzugefügt am 29.05.2025
        case "synthseg-model:brainns":
            return {
                "image": "synthseg-model:brainns",
                "container_name": f'SynthSeg_container_{segmentation_id}',
                #                 "command": ["conda", "run", "-n" "synthseg_env", "python", "SynthSeg/scripts/commands/SynthSeg_predict.py", "--i", "/app/input", "--o", '/app/output', "--cpu", "--threads", "6", "--resample", "/app/output/resampled"],
                "command": ["conda", "run", "-n" "synthseg_env", "python", "SynthSeg/scripts/commands/SynthSeg_predict.py", "--i", "/app/input", "--o", '/app/output',"--parc", "--cpu", "--threads", "6", "--resample", "/app/output/resampled"],
                "output_path": '/app/output',
                "docker_file_path": "/usr/src/models/SynthSeg",
                "uses_gpu": True,
                "necessarySequences": ["t2"],
                "skipPreprocessing": True,
                "resampledDataExists": True
            }

        case _:
            print("The model doesn't exist.")
            raise Exception(f"The model {model} doesn't exist.")