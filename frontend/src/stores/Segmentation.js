export class Segmentation {
    
    // The segmentation ID, as stored in the DB. Initialized with -1 because we don't have the DB's ID upon creation of a
    // Segmentation object.
    segmentationID = -1

    // The segmentation name is given by the user before starting a segmentation
    segmentationName = ""

    // The date and time of the start of the segmentation, as determined by the DB
    dateTime = ""

    // The selected model for the segmentation
    model = ""
    
    // For each of the four sequences, this is a mapping to the corresponding folder/file name
    // of each sequence.
    selectedSequences = 
    {
        flair: {},
        t1: {},
        t1km: {},
        t2: {}
    }

    // The status of the segmentation, as given by the Store
    status = SegmentationStatus.PREPROCESSING

    // The actual segmentation data
    data = null

    toString() {
        return `Segmentation {
            segmentationID: ${this.segmentationID},
            segmentationName: "${this.segmentationName}",
            dateTime: "${this.dateTime}",
            model: "${this.model}",
            selectedSequences: {
                flair: "${this.selectedSequences.flair}",
                t1: "${this.selectedSequences.t1}",
                t1km: "${this.selectedSequences.t1km}",
                t2: "${this.selectedSequences.t2}"
            },
            data: ${this.data !== null ? JSON.stringify(this.data) : null}
        }`
    }
}


export const SegmentationStatus = {
    PREPROCESSING: {id: "PREPROCESSING", displayName: "Preprocessing", svgPath: ""},
    PREDICTING: {id: "PREDICTING", displayName: "Vorhersage", svgPath: ""},
    DONE: {id: "DONE", displayName: "Fertig", svgPath: ""},
    ERROR: {id: "ERROR", displayName: "Fehler", svgPath: ""},
}