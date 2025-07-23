from server.database import db
from datetime import datetime, timezone, timedelta

token_expire_time_in_hours = 24

# User model
class User(db.Model):
    __tablename__ = 'users'
    
    user_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_mail = db.Column(db.String(255), nullable=False, unique=True) 
    password_hash = db.Column(db.String(255), nullable=False)  
    registration_date = db.Column(db.DateTime, default=datetime.now(timezone.utc), nullable=False)

    # Relationships
    sessions = db.relationship('Session', backref='user', lazy=True)
    projects = db.relationship('Project', backref='user', lazy=True)

# User Settings model
class UserSettings(db.Model):
    """A class for all user settings. Each one should get a default value on creation of a user.
    These columns are not part of the User table for clarity."""
    __tablename__ = "user_settings"

    user_id = db.Column(db.Integer, db.ForeignKey("users.user_id"), primary_key=True, nullable=False)
    confirm_delete_entry = db.Column(db.Boolean, default=True, nullable=False)
    number_displayed_recent_segmentations = db.Column(db.Integer, default=1000000, nullable=False)
    default_download_type = db.Column(db.String(255), default="nifti", nullable=False)
    min_max_window_leveling = db.Column(db.Boolean, default=False, nullable=False)

# Session model
class Session(db.Model):
    __tablename__ = 'sessions'
    
    session_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False)
    session_token = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.now(timezone.utc), nullable=False)
    expires_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc) + timedelta(hours=token_expire_time_in_hours), nullable=False)

# Whitelist model
class Whitelist(db.Model):
    __tablename__ = 'whitelist'
    # whitelist_id not needed, as long as user_mail can be used as primary key
    # whitelist_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_mail = db.Column(db.String(255), primary_key=True, nullable=False, unique=True) 

# Project model
class Project(db.Model):
    __tablename__ = 'projects'
    
    project_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False)
    project_name = db.Column(db.String(255), nullable=False)
    file_format = db.Column(db.String(255), nullable=False)

    # Relationships
    segmentations = db.relationship('Segmentation', backref='project', cascade='all, delete', lazy=True)
    sequences = db.relationship('Sequence', backref='project', cascade='all, delete', lazy=True)


# Sequence model
class Sequence(db.Model):
    __tablename__ = 'sequences'
    
    sequence_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    project_id = db.Column(db.Integer, db.ForeignKey('projects.project_id', ondelete='CASCADE'), nullable=False)
    sequence_name = db.Column(db.String(255), nullable=False)  # Original filename
    sequence_type = db.Column(db.String(50), nullable=False)  # e.g., t1, t2, etc
    classified_sequence_type = db.Column(db.String(50), nullable=True) # The sequence type assigned by the classifier
    acquisition_plane = db.Column(db.String(50), nullable=True) # e.g., cor, sag, ax
    resolution = db.Column(db.Float, nullable=True)
    size_in_bytes = db.Column(db.Integer, nullable=True)
    selected = db.Column(db.Boolean, nullable=False)

    # Relationships
    t1_segmentations = db.relationship('Segmentation', backref='t1_sequence_rel', foreign_keys='Segmentation.t1_sequence', lazy=True)
    t1km_segmentations = db.relationship('Segmentation', backref='t1km_sequence_rel', foreign_keys='Segmentation.t1km_sequence', lazy=True)
    t2_segmentations = db.relationship('Segmentation', backref='t2_sequence_rel',  foreign_keys='Segmentation.t2_sequence', lazy=True)
    flair_segmentations = db.relationship('Segmentation', backref='flair_sequence_rel', foreign_keys='Segmentation.flair_sequence', lazy=True)


# Segmentation model
class Segmentation(db.Model):
    __tablename__ = 'segmentations'
    
    segmentation_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    project_id = db.Column(db.Integer, db.ForeignKey('projects.project_id', ondelete='CASCADE'), nullable=False)
    t1_sequence = db.Column(db.Integer, db.ForeignKey('sequences.sequence_id', ondelete='CASCADE'))
    t1km_sequence = db.Column(db.Integer, db.ForeignKey('sequences.sequence_id', ondelete='CASCADE'))
    t2_sequence = db.Column(db.Integer, db.ForeignKey('sequences.sequence_id', ondelete='CASCADE'))
    flair_sequence = db.Column(db.Integer, db.ForeignKey('sequences.sequence_id', ondelete='CASCADE'))
    display_values = db.Column(db.Integer, db.ForeignKey('display_values.display_values_id', ondelete='CASCADE'), nullable=False)
    model = db.Column(db.String(255), nullable=False)
    preprocessing_id = db.Column(db.String(255), nullable=True)
    prediction_id = db.Column(db.String(255), nullable=True)
    date_time = db.Column(db.DateTime, default=datetime.now(timezone.utc), nullable=False)
    segmentation_name = db.Column(db.String(255), nullable=False)
    status = db.Column(db.String(255), nullable=False)


class DisplayValues(db.Model):
    __tablename__ = 'display_values'

    display_values_id = db.Column(db.Integer, primary_key=True, autoincrement=True)

    # The minimum and maximum pixel values of the preprocessed dicom series (used for window leveling)
    flair_min_display_value_custom = db.Column(db.Integer, nullable=True) 
    flair_max_display_value_custom = db.Column(db.Integer, nullable=True) 
    flair_min_display_value_by_dicom_tag = db.Column(db.Integer, nullable=True) 
    flair_max_display_value_by_dicom_tag = db.Column(db.Integer, nullable=True)
    t1_min_display_value_custom = db.Column(db.Integer, nullable=True)
    t1_max_display_value_custom = db.Column(db.Integer, nullable=True) 
    t1_min_display_value_by_dicom_tag = db.Column(db.Integer, nullable=True) 
    t1_max_display_value_by_dicom_tag = db.Column(db.Integer, nullable=True) 
    t2_min_display_value_custom = db.Column(db.Integer, nullable=True)
    t2_max_display_value_custom = db.Column(db.Integer, nullable=True)
    t2_min_display_value_by_dicom_tag = db.Column(db.Integer, nullable=True) 
    t2_max_display_value_by_dicom_tag = db.Column(db.Integer, nullable=True)
    t1km_min_display_value_custom = db.Column(db.Integer, nullable=True) 
    t1km_max_display_value_custom = db.Column(db.Integer, nullable=True) 
    t1km_min_display_value_by_dicom_tag = db.Column(db.Integer, nullable=True) 
    t1km_max_display_value_by_dicom_tag = db.Column(db.Integer, nullable=True) 