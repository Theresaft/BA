# Based on https://simpleitk.readthedocs.io/en/next/Examples/DicomSeriesFromArray/Documentation.html

from __future__ import print_function

import SimpleITK as sitk

import time, os
import numpy as np

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

def convert_base_image_to_dicom_sequence(nifti_image_path, dest_path, dicom_tag_src_path=""):
    # Create a new series from a numpy array
    # Converted to UInt 16 so that the Viewer can handle it
    new_img = sitk.Cast(sitk.ReadImage(nifti_image_path), sitk.sitkUInt16)

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

    reader = sitk.ImageSeriesReader()
    if dicom_tag_src_path:
        # Use the ImageSeriesReader to get the list of DICOM files in the series to get the header informations from
        dicom_files = reader.GetGDCMSeriesFileNames(dicom_tag_src_path)

        # Extract the first slice
        source_image = sitk.ReadImage(os.path.join(dicom_tag_src_path, dicom_files[0]))  # Extracting the first slice along the z-axis

        # Extract the header information
        for key in source_image.GetMetaDataKeys():
            if key in ["0008|0031", "0008|0021", "0020|0037"]:
                continue
            value = source_image.GetMetaData(key)
            series_tag_values.append((key, value.encode("utf-8", errors="replace").decode()))

    # Set series Description to missing if not set
    if not "0008|103e" in list(map(lambda e: e[0], series_tag_values)):
        series_tag_values.append(("0008|103e", "Missing"))

    # Set seriesID to missing if not set
    if not "0020|000e" in list(map(lambda e: e[0], series_tag_values)):
        series_tag_values.append(("0020|000e", "Missing"))

    # Set Image Type if not set
    if not "0008|0008" in list(map(lambda e: e[0], series_tag_values)):
        series_tag_values.append(("0008|0008","DERIVED\\SECONDARY"))

    # Write slices to output directory
    list(map(lambda i: writeSlices(series_tag_values, new_img, i, writer, dest_path), range(new_img.GetDepth())))


def convert_base_image_to_3d_dicom(nifti_image_path, dest_path, dicom_tag_src_path=""):
    # Create a new series from a numpy array
    # Converted to UInt 16 so that the Viewer can handle it
    new_img = sitk.Cast(sitk.ReadImage(nifti_image_path), sitk.sitkUInt16)

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
    if dicom_tag_src_path:
        dicom_files = reader.GetGDCMSeriesFileNames(dicom_tag_src_path)

        # Extract the first slice
        source_image = sitk.ReadImage(os.path.join(dicom_tag_src_path, dicom_files[0]))  # Extracting the first slice along the z-axis

        # Extract the header information
        for key in source_image.GetMetaDataKeys():
            if key in ["0008|0031", "0008|0021", "0020|0037"]:
                continue
            value = source_image.GetMetaData(key)
            series_tag_values.append((key, value.encode("utf-8", errors="replace").decode()))

    # Set series Description to missing if not set
    if not "0008|103e" in list(map(lambda e: e[0], series_tag_values)):
        series_tag_values.append(("0008|103e", "Missing"))

    # Set seriesID to missing if not set
    if not "0020|000e" in list(map(lambda e: e[0], series_tag_values)):
        series_tag_values.append(("0020|000e", "Missing"))

    # Set Image Type if not set
    if not "0008|0008" in list(map(lambda e: e[0], series_tag_values)):
        series_tag_values.append(("0008|0008","DERIVED\\SECONDARY"))

    list(map(lambda tag_value: new_img.SetMetaData(tag_value[0], tag_value[1]), series_tag_values))

    # Setting the type to CT preserves the slice location.
    new_img.SetMetaData("0008|0060", "CT")  # set the type to CT so the thickness is carried over

    # Write to the output directory and add the extension dcm, to force writing in DICOM format.
    file_name = os.path.basename(nifti_image_path).split('.')[0] + '.dcm'
    writer.SetFileName(os.path.join(dest_path, file_name))
    writer.Execute(new_img)


def convert_segmentation_to_3d_dicom(nifti_segmentation_path, output_dicom_path):
    """
    Converts a NIfTI segmentation file to a single 3D DICOM image.

    Parameters:
        nifti_segmentation_path (str): Path to the NIfTI segmentation file.
        output_dicom_path (str): Path to save the output 3D DICOM file.
    """
    # Read the segmentation image and cast it to UInt16 for compatibility.
    # segmentation_image = sitk.Cast(sitk.ReadImage(nifti_segmentation_path), sitk.sitkUInt8)

    # Read the segmentation image.
    segmentation_image_float = sitk.Cast(sitk.ReadImage(nifti_segmentation_path), sitk.sitkUInt16)
    
    # Convert the segmentation to UInt8 (integer type), rounding the values as necessary
    # If the segmentation contains fractional values (e.g., probabilities), threshold or round it to integers.
    segmentation_array = sitk.GetArrayFromImage(segmentation_image_float)
    
    # Convert fractional segmentations to integers (e.g., 0 or 1 for binary segmentation).
    # This can be done by thresholding at 0.5 for binary segmentations.
    thresholded_segmentation_array = (segmentation_array > 0.5).astype(np.uint8)  # Threshold to binary (0, 1)
    
    # Convert back to a SimpleITK image with the corrected integer type.
    segmentation_image = sitk.GetImageFromArray(thresholded_segmentation_array)
    segmentation_image.CopyInformation(segmentation_image_float)  # Keep metadata



    # Create a writer to save the 3D DICOM image.
    writer = sitk.ImageFileWriter()
    writer.KeepOriginalImageUIDOn()

    # Generate some basic DICOM metadata tags.
    modification_time = time.strftime("%H%M%S")
    modification_date = time.strftime("%Y%m%d")

    # Set required DICOM tags for a 3D image.
    segmentation_image.SetMetaData("0008|0031", modification_time)  # Series Time
    segmentation_image.SetMetaData("0008|0021", modification_date)  # Series Date
    segmentation_image.SetMetaData("0008|0060", "SEG")  # Modality
    segmentation_image.SetMetaData("0020|000D", "2.25.544874479662469874311086145752052251264")  # Study Instance UID 	
    segmentation_image.SetMetaData("0020|000E", "2.25.930886299744262508560729108693647177710")  # Series Instance UID
    segmentation_image.SetMetaData("0008|103E", "Segmentation")  # Series Description
    segmentation_image.SetMetaData("0008|0008", "DERIVED\\PRIMARY")  # Image Type

    # Set additional metadata based on the segmentation's physical properties.
    direction = segmentation_image.GetDirection()
    segmentation_image.SetMetaData("0020|0037", '\\'.join(map(str, (
        direction[0], direction[3], direction[6],
        direction[1], direction[4], direction[7]
    ))))  # Image Orientation (Patient)

    # VERY QUESTIONABLE:
    segmentation_image.SetMetaData("0020|0032", '\\'.join(map(str, segmentation_image.GetOrigin())))  # Image Position (Patient)
    segmentation_image.SetMetaData("0028|0030", '\\'.join(map(str, segmentation_image.GetSpacing()[:2])))  # Pixel Spacing
    # Set pixel spacing for the third dimension (slice thickness).
    segmentation_image.SetMetaData("0018|0050", str(segmentation_image.GetSpacing()[2]))  # Slice Thickness

    segmentation_image.SetMetaData("0008|0016", "1.2.840.10008.5.1.4.1.1.66.4") # SOPClassUID
    segmentation_image.SetMetaData("0070|0080", "SEGMENTATION") # Content Label
    segmentation_image.SetMetaData("0070|0081", "some description") # Content Description
    segmentation_image.SetMetaData("0062|0001", "BINARY") # Segmentation Type

    # Segment Sequence
    # segmentation_image.SetMetaData("0008|0100", "T-D0050")  # Code Value
    # segmentation_image.SetMetaData("0008|0102", "SRT")      # Coding Scheme Designator
    # segmentation_image.SetMetaData("0008|0104", "Tissue")   # Code Meaning
    # segmentation_image.SetMetaData("0062|0004", "1")     # Segment Number 
    # segmentation_image.SetMetaData("0062|0005", "Segment 1") # Segment Label
    # segmentation_image.SetMetaData("0062|0008", "MANUAL")    # Segment Algorithm Type
    # segmentation_image.SetMetaData("0062|000D", '\\'.join(map(str, [35650, 46654, 40238])))  # Recommended Display CIELab Value
    # segmentation_image.SetMetaData("0062|0002",  "[(0062,0003)  Segmented Property Category Code Sequence  1 item(s) ---- \n   (0008,0100) Code Value                          SH: 'T-D0050'\n   (0008,0102) Coding Scheme Designator            SH: 'SRT'\n   (0008,0104) Code Meaning                        LO: 'Tissue'\n   ---------\n(0062,0004) Segment Number                      US: 1\n(0062,0005) Segment Label                       LO: 'Segment 1'\n(0062,0008) Segment Algorithm Type              CS: 'MANUAL'\n(0062,000D) Recommended Display CIELab Value    US: [35650, 46654, 40238]\n(0062,000F)  Segmented Property Type Code Sequence  1 item(s) ---- \n   (0008,0100) Code Value                          SH: 'T-D0050'\n   (0008,0102) Coding Scheme Designator            SH: 'SRT'\n   (0008,0104) Code Meaning                        LO: 'Tissue'\n   ---------]")

    # Write the 3D segmentation image to the output path as a DICOM file.
    writer.SetFileName(output_dicom_path)
    writer.Execute(segmentation_image)



# convert_segmentation_to_3d_dicom("./data/.nii.gz", "./data/segmentation.dcm")
