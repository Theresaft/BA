import os
import logging
from dataclasses import dataclass
import SimpleITK as sitk

BASEDIR = './'
# BASEDIR = '/data_marvin2/ehrhardt/projects/Fallstudie/NeuralPreProcessing'
# BASEDIR = '/share/data_animal1/ehrhardt/StudentProjects/FallstudieSS24/NeuralPreprocessing'
DATADIR = os.path.join(BASEDIR, 'input')
RESULTDIR = os.path.join(BASEDIR, 'output')
WRKDIR = os.path.join(BASEDIR, 'temp')
FSLDIR = './fsl'
# FSLDIR = os.path.join(BASEDIR, 'FSL')
# FSLDIR = '/data_marvin2/ehrhardt/projects/Fallstudie/NeuralPreProcessing/FSL'

SequenceNames = ('t1c', 't1', 't2', 'flair')
ReferenceSequence = 't1c'
RequiredSequences = ('t1c', 't1', 't2', 'flair')


@dataclass
class SubjectConfig:
    subject_id: str
    input_base_dir: str = DATADIR
    output_base_dir: str = RESULTDIR
    working_dir: str = WRKDIR
    input_files = dict({seq: None for seq in SequenceNames})
    input_meta = dict({seq: None for seq in SequenceNames})
    skullstrip_files = dict()  # a dictionary sequence -> Filename
    resample_files = dict()  # a dictionary sequence -> Filename
    register_files = dict()  # a dictionary sequence -> Filename
    reference_seq: str = ReferenceSequence
    same_coordinates = dict()
    # same_coordinates = dict({'t2': ['t1', 'flair'], 'flair': ['t1', 't2'], 't1': ['flair', 't2']})  # a dictionary sequence -> sequence to save which sequence is co_registered to which other
    label_sequences = []  # list of sequences that are labels or segmentation (e.g. for adequat interpolation)

    def get_output_dir(self):
        assert os.path.isdir(self.output_base_dir)
        return os.path.join(self.output_base_dir, self.subject_id)

    def get_working_dir(self):
        assert os.path.isdir(self.working_dir)
        return self.working_dir

    def init_filenames(self):
        for seq in self.input_files.keys():
            fname = self.get_input_filename(seq)
            self.input_files[seq] = fname if os.path.exists(fname) else None
        skullstrip_sequences = ['brainmask', 'scalar_field']
        # only set other files if not already set/updated
        for seq in [s for s in skullstrip_sequences if not s in self.skullstrip_files]:
            self.skullstrip_files[seq] = os.path.join(self.get_working_dir(), f"{self.subject_id}_{seq}.nii.gz")
        resample_sequences = list(self.input_files.keys()) + skullstrip_sequences + ['resample_mask']
        for seq in [s for s in resample_sequences if not s in self.resample_files]:
            if not seq in self.input_files.keys() or self.input_files[seq] is not None:
                self.resample_files[seq] = os.path.join(self.get_working_dir(), f"{self.subject_id}_{seq}_resample.nii.gz")
        for seq in [s for s in resample_sequences if not s in self.register_files]:
            if not seq in self.input_files.keys() or self.input_files[seq] is not None:
                self.register_files[seq] = os.path.join(self.get_working_dir(), f"{self.subject_id}_{seq}_register.nii.gz")

    def init_meta(self):
        self.init_filenames()
        for seq in self.input_files.keys():
            if self.input_files[seq] is not None and os.path.exists(self.input_files[seq]):
                reader = sitk.ImageFileReader()
                reader.SetFileName(self.input_files[seq])
                reader.LoadPrivateTagsOn()
                reader.ReadImageInformation()
                meta_dict = {'dim': reader.GetDimension(), 'origin': reader.GetOrigin(),
                             'spacing': reader.GetSpacing(), 'direction': reader.GetDirection()}
                for k in reader.GetMetaDataKeys():
                    v = reader.GetMetaData(k)
                    meta_dict[k] = v
                self.input_meta[seq] = meta_dict

    def get_input_filename(self, seq: str):
        assert os.path.isdir(self.input_base_dir)
        return os.path.join(self.input_base_dir, self.subject_id, f"{self.subject_id}_{seq}.nii.gz")


def setup_logger(logger_name, logfile, level=logging.DEBUG):
    #assert not os.path.dirname(logfile) or os.path.isdir(os.path.dirname(logfile)), ""
    if os.path.exists(logfile):
        os.rename(logfile, logfile + ".bak")

    logger = logging.getLogger(logger_name)
    logFormatter = logging.Formatter("%(asctime)s [%(levelname)-5.5s]  %(message)s")
    fileHandler = logging.FileHandler(logfile, mode='w')
    fileHandler.setFormatter(logFormatter)
    consoleHandler = logging.StreamHandler()
    consoleHandler.setFormatter(logFormatter)

    logger.setLevel(level)
    logger.addHandler(consoleHandler)
    logger.addHandler(fileHandler)
    return logger
