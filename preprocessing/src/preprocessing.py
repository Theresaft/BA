import SimpleITK as sitk
import os

input_path = "input"
output_path = "output"

for seq in ["flair", "t1", "t1km", "t2"]:
    src_path = os.path.join(input_path, str(seq))
        
    # Read DICOM Sequence
    series_reader = sitk.ImageSeriesReader()
    series_filenames = series_reader.GetGDCMSeriesFileNames(src_path)
    series_reader.SetFileNames(series_filenames)
    image_data = series_reader.Execute()

    # Convert DICOM to NIFTI
    nifti_output_path = os.path.join(output_path, f'{seq}.nii.gz')
    sitk.WriteImage(image_data, nifti_output_path)