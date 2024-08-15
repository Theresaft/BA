# server/main/dicom_classifier.py
from dcm_classifier.study_processing import ProcessOneDicomStudyToVolumesMappingBase
from dcm_classifier.image_type_inference import ImageTypeClassifierBase
from pathlib import Path
import pydicom
import os


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

    t1=[]
    t1km = []
    t2=[]
    flair=[]

    for series_number, series in study.series_dictionary.items():
        for index, volume in enumerate(series.get_volume_list()):
            volume_filename = volume.get_one_volume_dcm_filenames()[0]
            name = getCorrectPath(volume_filename)
            if volume.get_volume_modality() == "t1w":
                if volume.get_has_contrast() or "KM" in volume.get_volume_series_description():
                    t1km.append(name)
                else:
                    t1.append(name)
            if volume.get_volume_modality() == "t2w":
                t2.append(name)
            if volume.get_volume_modality() == "flair":
                flair.append(name)

    results = {
        "t1" : t1,
        "t1km" : t1km,
        "t2" : t2,
        "flair" : flair
    }

    return results


def getCorrectPath(path):
    splitpath = str(path).split("\\")
    relevant_path = splitpath[splitpath.index("dicom-images")+2:len(splitpath)-1]
    return "/".join(relevant_path) + "/"

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