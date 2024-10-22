# Use the PyTorch image with CUDA 12.1 support
FROM python:3.12-slim

# Set the working directory in the container
WORKDIR /app
RUN mkdir input

# add requirements (to leverage Docker cache)
COPY ./requirements.txt /app/requirements.txt

# install requirements
RUN pip install -r requirements.txt

# COPY the preprocessing source code
COPY /src/ /app/