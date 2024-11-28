from server.database import db
from datetime import datetime, timezone


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

# Session model
class Session(db.Model):
    __tablename__ = 'sessions'
    
    session_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False)
    session_token = db.Column(db.String(255), nullable=False)

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
    segmentations = db.relationship('Segmentation', backref='project', lazy=True)
    sequences = db.relationship('Sequence', backref='project', lazy=True)


# Sequence model
class Sequence(db.Model):
    __tablename__ = 'sequences'
    
    sequence_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    project_id = db.Column(db.Integer, db.ForeignKey('projects.project_id'), nullable=False)
    sequence_name = db.Column(db.String(255), nullable=False)  # Original filename
    sequence_type = db.Column(db.String(50), nullable=False)  # e.g., t1, t2, etc
    classified_sequence_type = db.Column(db.String(50), nullable=True) # The sequence type assigned by the classifier
    acquisition_plane = db.Column(db.String(50), nullable=True) # e.g., cor, sag, ax
    resolution = db.Column(db.Float, nullable=True)


    # Relationships
    t1_segmentations = db.relationship('Segmentation', backref='t1_sequence_rel', foreign_keys='Segmentation.t1_sequence', lazy=True)
    t1km_segmentations = db.relationship('Segmentation', backref='t1km_sequence_rel', foreign_keys='Segmentation.t1km_sequence', lazy=True)
    t2_segmentations = db.relationship('Segmentation', backref='t2_sequence_rel',  foreign_keys='Segmentation.t2_sequence', lazy=True)
    flair_segmentations = db.relationship('Segmentation', backref='flair_sequence_rel', foreign_keys='Segmentation.flair_sequence', lazy=True)


# Segmentation model
class Segmentation(db.Model):
    __tablename__ = 'segmentations'
    
    segmentation_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    project_id = db.Column(db.Integer, db.ForeignKey('projects.project_id'), nullable=False)
    t1_sequence = db.Column(db.Integer, db.ForeignKey('sequences.sequence_id'), nullable=False)
    t1km_sequence = db.Column(db.Integer, db.ForeignKey('sequences.sequence_id'), nullable=False)
    t2_sequence = db.Column(db.Integer, db.ForeignKey('sequences.sequence_id'), nullable=False)
    flair_sequence = db.Column(db.Integer, db.ForeignKey('sequences.sequence_id'), nullable=False)
    model = db.Column(db.String(255), nullable=False)
    preprocessing_id = db.Column(db.String(255), nullable=True)
    prediction_id = db.Column(db.String(255), nullable=True)
    date_time = db.Column(db.DateTime, default=datetime.now(timezone.utc), nullable=False)
    segmentation_name = db.Column(db.String(255), nullable=False)
    status = db.Column(db.String(255), nullable=False)
