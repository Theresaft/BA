export class Project {
    // The project ID, as stored in the DB
    projectID = -1
    // The project name is given by the user when creating a project
    projectName = ""
    fileType = ""
    // A list of Segmentation objects
    segmentations = []
    // A list of Sequence objects
    sequences = []

    toString() {
        return `Project {
            projectID: ${this.projectID},
            projectName: "${this.projectName}",
            fileType: "${this.fileType}",
            segmentations: [
                ${this.segmentations.map(segmentation => segmentation.toString()).join(",\n        ")}
            ],
            sequences: [
                ${this.sequences.map(sequence => sequence.toString()).join(",\n        ")}
            ]
        }`
    }
}