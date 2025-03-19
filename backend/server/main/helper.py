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