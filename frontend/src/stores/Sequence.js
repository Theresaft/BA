export class Sequence {
    // The sequence ID, as stored in the DB
    sequenceID = -1
    // The sequence name is the folder name of this sequence (including "/")
    sequenceName = ""
    // The plane from which the recording was done
    acquisitionPlane = ""
    // A list of the file names in the sequence
    fileNames = []
    // A list of the file contents
    files = []
    // The image resolution
    resolution = 0.0
    // Whether the user has selected this sequence in the project selection
    selected = false
    // The sequence type given by the user
    sequenceType = ""
    // The sequence type that was auto-generated from the metadata of the file
    classifiedSequenceType = ""

    toString() {
        return `Sequence {
            sequenceID: ${this.sequenceID},
            sequenceName: "${this.sequenceName}",
            acquisitionPlane: "${this.acquisitionPlane}",
            fileNames: [${this.fileNames.map(fileName => `"${fileName}"`).join(", ")}],
            files: [${this.files.map(file => `"${file}"`).join(", ")}],
            resolution: ${this.resolution},
            selected: ${this.selected},
            sequenceType: "${this.sequenceType}",
            classifiedSequenceType: "${this.classifiedSequenceType}"
        }`
    }
}