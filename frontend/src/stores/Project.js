import "./Segmentation.js"

class Project {
    // The project ID, as stored in the DB
    projectID = -1
    // The project name is given by the user when creating a project
    projectName = ""
    fileType = "DICOM"
    // A list of Segmentation objects
    segmentations = []
    // A list of Sequence objects
    sequences = []
}