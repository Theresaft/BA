class Segmentation {
    // The segmentation ID, as stored in the DB
    segmentationID = -1
    // The segmentation name is given by the user before starting a segmentation
    segmentationName = ""
    // The date and time of the start of the segmentation, as determined by the DB
    dateTime = ""
    // The selected model for the segmentation
    model = ""
    // For each of the four sequences, this is a mapping to the corresponding folder name
    // of each sequence.
    selectedSequences = 
    {
        flair: "",
        t1: "",
        t1km: "",
        t2: ""
    }
    // The actual segmentation data
    data = null
}