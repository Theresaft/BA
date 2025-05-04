# Use the Python 3.8 image
FROM python:3.8-slim

# Set the working directory in the container
WORKDIR /app

# Install required packages, including gcc and lbzip2 (as root)
RUN apt-get update && apt-get install -y gcc lbzip2

# Create brainns user and group with fixed UID and GID
RUN groupadd -g 1050 brainns && \
    useradd -m -u 1050 -g 1050 brainns

# Create directories as root
RUN mkdir input
RUN mkdir input/nifti
RUN mkdir input/dicom
RUN mkdir temp

# Change the ownership of the directories to brainns
RUN chown -R brainns:brainns /app/input /app/temp

# COPY the preprocessing source code
COPY --chown=brainns:brainns /src /app

# Install fsl as root (change permissions afterwards)
RUN python fslinstaller.py --dest /app/fsl --no_env --skip_registration && \
    chown -R brainns:brainns /app/fsl

# Switch to brainns user
USER brainns

# Add requirements (to leverage Docker cache)
COPY --chown=brainns:brainns ./requirements.txt /app/requirements.txt

# Install requirements
RUN pip install -r requirements.txt
