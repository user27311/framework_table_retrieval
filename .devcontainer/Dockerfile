FROM mcr.microsoft.com/devcontainers/python:3.10-bullseye
RUN sudo apt update
RUN sudo apt install ffmpeg libsm6 libxext6 libpoppler-dev poppler-utils -y --no-install-recommends
RUN apt-get update && apt-get install -y \
	git \
	openjdk-17-jdk \
	openjdk-17-jre 
	
WORKDIR /workspaces
ADD . /workspaces
