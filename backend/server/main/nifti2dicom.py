# Based on https://simpleitk.readthedocs.io/en/next/Examples/DicomSeriesFromArray/Documentation.html

from __future__ import print_function

import SimpleITK as sitk

import time, os

def writeSlices(series_tag_values, new_img, i, writer, dest_path):
    image_slice = new_img[:,:,i]

    # Tags shared by the series.
    list(map(lambda tag_value: image_slice.SetMetaData(tag_value[0], tag_value[1]), series_tag_values))

    # Slice specific tags.
    image_slice.SetMetaData("0008|0012", time.strftime("%Y%m%d")) # Instance Creation Date
    image_slice.SetMetaData("0008|0013", time.strftime("%H%M%S")) # Instance Creation Time

    # Setting the type to CT preserves the slice location.
    image_slice.SetMetaData("0008|0060", "CT")  # set the type to CT so the thickness is carried over

    # (0020, 0032) image position patient determines the 3D spacing between slices.
    image_slice.SetMetaData("0020|0032", '\\'.join(map(str,new_img.TransformIndexToPhysicalPoint((0,0,i))))) # Image Position (Patient)
    image_slice.SetMetaData("0020,0013", str(i)) # Instance Number

    # Write to the output directory and add the extension dcm, to force writing in DICOM format.
    writer.SetFileName(os.path.join(dest_path,str(i)+'.dcm'))
    writer.Execute(image_slice)

def convert_base_image(nifti_image_path, dest_path, dicom_tag_src_path):
    # Create a new series from a numpy array
    new_img = sitk.ReadImage(nifti_image_path)

    os.mkdir(dest_path)

    # Write the 3D image as a series
    # IMPORTANT: There are many DICOM tags that need to be updated when you modify an
    #            original image. This is a delicate opration and requires knowlege of
    #            the DICOM standard. This example only modifies some. For a more complete
    #            list of tags that need to be modified see:
    #                           http://gdcm.sourceforge.net/wiki/index.php/Writing_DICOM
    #            If it is critical for your work to generate valid DICOM files,
    #            It is recommended to use David Clunie's Dicom3tools to validate the files 
    #                           (http://www.dclunie.com/dicom3tools.html).

    writer = sitk.ImageFileWriter()
    # Use the study/series/frame of reference information given in the meta-data
    # dictionary and not the automatically generated information from the file IO
    writer.KeepOriginalImageUIDOn()

    modification_time = time.strftime("%H%M%S")
    modification_date = time.strftime("%Y%m%d")

    # Copy some of the tags and add the relevant tags indicating the change.
    # For the series instance UID (0020|000e), each of the components is a number, cannot start
    # with zero, and separated by a '.' We create a unique series ID using the date and time.
    # tags of interest:
    direction = new_img.GetDirection()

    series_tag_values = [("0008|0031",modification_time), # Series Time
                    ("0008|0021",modification_date), # Series Date
                    ("0020|0037", '\\'.join(map(str, (direction[0], direction[3], direction[6],# Image Orientation (Patient)
                                                        direction[1],direction[4],direction[7]))))]

    # Use the ImageSeriesReader to get the list of DICOM files in the series to get the header informations from
    reader = sitk.ImageSeriesReader()
    dicom_files = reader.GetGDCMSeriesFileNames(dicom_tag_src_path)

    # Extract the first slice
    source_image = sitk.ReadImage(os.path.join(dicom_tag_src_path, dicom_files[0]))  # Extracting the first slice along the z-axis

    # Extract the header information
    for key in source_image.GetMetaDataKeys():
        if key == "0008|0031" or "0008|0021" or "0020|0037":
            continue
        value = source_image.GetMetaData(key)
        series_tag_values.append(key, value.encode("utf-8", errors="replace").decode())

    # Set series Description to missing if not set
    if not "0008|103e" in list(map(lambda e: e[0], series_tag_values)):
        print("0008|103e")
        series_tag_values.append(("0008|103e", "Missing"))

    # Set seriesID to missing if not set
    if not "0020|000e" in list(map(lambda e: e[0], series_tag_values)):
        print("0020|000e")
        series_tag_values.append(("0020|000e", "Missing"))

    # Set Image Type if not set
    if not "0008|0008" in list(map(lambda e: e[0], series_tag_values)):
        print("0008|0008")
        series_tag_values.append(("0008|0008","DERIVED\\SECONDARY"))

    # Write slices to output directory
    list(map(lambda i: writeSlices(series_tag_values, new_img, i, writer, dest_path), range(new_img.GetDepth())))