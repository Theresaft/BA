# Basisimage: Miniconda mit Python 3.8
FROM continuumio/miniconda3

# Arbeitsverzeichnis im Container
WORKDIR /app

# Create brainns user and group with fixed UID and GID (match host)
RUN groupadd -g 1050 brainns && \
    useradd -m -u 1050 -g 1050 brainns

# Erstelle und aktiviere conda-Umgebung mit Python 3.8
RUN conda create -y -n synthseg_env python=3.8 tensorflow-gpu=2.2.0 keras=2.3.1 nibabel matplotlib -c anaconda -c conda-forge && \
    conda run -n synthseg_env python --version && \
    conda clean -afy

# Kopiere Projektdateien ins Container-Verzeichnis
COPY ./SynthSeg/requirements_python3.8.txt /app/SynthSeg/requirements_python3.8.txt

# Installiere Python-Abhängigkeiten aus requirements
RUN conda run -n synthseg_env pip install -r ./SynthSeg/requirements_python3.8.txt

# Create input directory and set permissions
RUN mkdir input && chown -R brainns:brainns /app
# RUN mkdir input

# Environment variable to avoid Matplotlib permission error
ENV MPLCONFIGDIR=/tmp/matplotlib

# Create necessary directories and set permissions
RUN mkdir -p /app/input /app/output /app/models /tmp/matplotlib && \
    chown -R brainns:brainns /app /tmp/matplotlib

# RUN mkdir -p /app/input /app/output /app/models /tmp/matplotlib

# Copy local SynthSeg directory and set permissions
COPY --chown=brainns:brainns SynthSeg/ /app/SynthSeg/
# COPY SynthSeg/ /app/SynthSeg/
