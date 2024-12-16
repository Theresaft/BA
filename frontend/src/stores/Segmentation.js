export class Segmentation {
    constructor({
        segmentationID = -1,
        segmentationName = "",
        projectName = "",
        dateTime = "",
        model = "",
        selectedSequences = {
            flair: {},
            t1: {},
            t1km: {},
            t2: {}
        },
        status = SegmentationStatus.QUEUEING,
        data = null
    } = {}) {
        this.segmentationID = segmentationID;
        this.segmentationName = segmentationName;
        this.projectName = projectName;
        this.dateTime = dateTime;
        this.model = model;
        this.selectedSequences = selectedSequences;
        this.status = status;
        this.data = data;
    }

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
    QUEUEING: {id: "QUEUEING", displayName: "Queueing", svgPath: ""},
    PREPROCESSING: {id: "PREPROCESSING", displayName: "Preprocessing", svgPath: ""},
    PREDICTING: {id: "PREDICTING", displayName: "Vorhersage", svgPath: ""},
    DONE: {id: "DONE", displayName: "Fertig", svgPath: ""},
    ERROR: {id: "ERROR", displayName: "Fehler", svgPath: ""},
}