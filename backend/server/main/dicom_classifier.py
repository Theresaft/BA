# server/main/dicom_classifier.py
from dcm_classifier.study_processing import ProcessOneDicomStudyToVolumesMappingBase
from dcm_classifier.image_type_inference import ImageTypeClassifierBase
from pathlib import Path
import pydicom


def classify(path):
    current_directory: Path = Path.cwd()

    session_directory = current_directory / path

    # create inferer object
    inferer = ImageTypeClassifierBase()

    # create study for given session directory
    study = ProcessOneDicomStudyToVolumesMappingBase(
        study_directory=session_directory.as_posix(), inferer=inferer
    )

    # run the inference on the study
    study.run_inference()

    t1 = []
    t1km = []
    t2 = []
    flair = []
    rest = []

    for series_number, series in study.series_dictionary.items():
        for index, volume in enumerate(series.get_volume_list()):
            volume_filename = volume.get_one_volume_dcm_filenames()[0]
            volume_object = {
                "path": get_correct_path(volume_filename),
                "resolution": get_resolution(volume_filename)
            }
            if volume.get_volume_modality() == "t1w":
                if has_contrast(volume_filename) or "km" in volume.get_volume_series_description().lower():
                    t1km.append(volume_object)
                else:
                    t1.append(volume_object)
            elif volume.get_volume_modality() == "t2w":
                t2.append(volume_object)
            elif volume.get_volume_modality() == "flair":
                flair.append(volume_object)
            else:
                description = volume.get_volume_series_description().lower()
                if "t1" in description:
                    if has_contrast(volume_filename) or "km" in description:
                        t1km.append(volume_object)
                    else:
                        t1.append(volume_object)
                elif "t2" in description:
                    t2.append(volume_object)
                elif "flair" in description:
                    flair.append(volume_object)
                else:
                    rest.append(volume_object)

    results = {
        "t1" : t1,
        "t1km" : t1km,
        "t2" : t2,
        "flair" : flair,
        "rest" : rest
    }

    return results


def has_contrast(path):
    ds = pydicom.dcmread(path)
    contrast_used = False

    if 'ContrastBolusAgent' in ds and ds.ContrastBolusAgent:
        contrast_used = True
    if 'ContrastBolusVolume' in ds and ds.ContrastBolusVolume > 0:
        contrast_used = True
    return contrast_used


def get_correct_path(path):
    splitpath = str(path).split("/")
    relevant_path = splitpath[splitpath.index("dicom-images")+2:len(splitpath)-1]
    return "/".join(relevant_path) + "/"


def get_resolution(path):
    ds = pydicom.dcmread(path)
    res = max(ds.SpacingBetweenSlices, ds.PixelSpacing[0], ds.PixelSpacing[1])
    return res


def get_best_resolution(files):
    ds = pydicom.dcmread(files[0])
    best_dicom = files[0]
    best_res = max(ds.SpacingBetweenSlices, ds.PixelSpacing[0], ds.PixelSpacing[1])
    for file in files:
        ds = pydicom.dcmread(file)
        res = max(ds.SpacingBetweenSlices, ds.PixelSpacing[0], ds.PixelSpacing[1])
        if res < best_res:
            best_dicom = file
            best_res = res
    path, seperator, file = str(best_dicom).rpartition("\\")
    return path