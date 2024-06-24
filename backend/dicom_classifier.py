from dcm_classifier.study_processing import ProcessOneDicomStudyToVolumesMappingBase
from dcm_classifier.image_type_inference import ImageTypeClassifierBase
from pathlib import Path


def is_complete(path):
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

    t1=False
    t2=False
    flair=False

    for series_number, series in study.series_dictionary.items():
        for index, volume in enumerate(series.get_volume_list()):
            if volume.get_volume_modality() == "t1w":
                t1=True
            if volume.get_volume_modality() == "t2w":
                t2=True
            if volume.get_volume_modality() == "flair":
                flair=True

    return t1, t2, flair