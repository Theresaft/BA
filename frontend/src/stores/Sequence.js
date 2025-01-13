export class Sequence {
    // The sequence ID, as stored in the DB
    sequenceID = -1
    // The plane from which the recording was done
    acquisitionPlane = ""
    // The image resolution
    resolution = 0.0
    // Whether the user has selected this sequence in the project selection
    selected = false
    // The sequence type given by the user
    sequenceType = "-"
    // The sequence type that was auto-generated from the metadata of the file
    classifiedSequenceType = "-"
    // The size of the sequence in bytes
    sizeInBytes = 0

    toString() {
        return `Sequence {
            sequenceID: ${this.sequenceID},
            acquisitionPlane: "${this.acquisitionPlane}",
            resolution: ${this.resolution},
            selected: ${this.selected},
            sequenceType: "${this.sequenceType}",
            classifiedSequenceType: "${this.classifiedSequenceType}"
        }`
    }
}

export class DicomSequence extends Sequence{
    // The sequence name is the folder name of this sequence (including "/")
    folder = ""
    // A list of the file names in the sequence
    fileNames = []
    // A list of the file contents
    files = []

    toString() {
        return `Sequence {
            sequenceID: ${this.sequenceID},
            folder: "${this.folder}",
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

export class NiftiSequence extends Sequence {
    // The nifti filename
    fileName = ""
    // The nifti file content
    file = null
    
    toString() {
        return `Sequence {
            sequenceID: ${this.sequenceID},
            fileName: "${this.fileName}",
            acquisitionPlane: "${this.acquisitionPlane}",
            file: "${this.file}",
            resolution: ${this.resolution},
            selected: ${this.selected},
            sequenceType: "${this.sequenceType}",
            classifiedSequenceType: "${this.classifiedSequenceType}"
        }`
    }
}