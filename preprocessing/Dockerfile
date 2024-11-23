# Use the Python 3.8 image
FROM python:3.8-slim

# Set the working directory in the container
WORKDIR /app
RUN mkdir input
RUN mkdir input/nifti
RUN mkdir temp

# COPY the preprocessing source code
COPY /src /app

# Install gcc
RUN apt-get update && apt-get install -y gcc

# Install fsl
RUN python fslinstaller.py --dest ./fsl --no_env --skip_registration

# add requirements (to leverage Docker cache)
COPY ./requirements.txt /app/requirements.txt

# install requirements
RUN pip install -r requirements.txt
