from python:3.7.13-alpine
COPY code/* /run/
COPY ../../downloader_backend.py /run/
RUN mkdir /settings
RUN python scheduler.py
