from python:3.7.13-alpine
COPY code/* /run/
RUN mkdir /settings
RUN python -m pip install -r /run/requirements.txt
RUN python /run/scheduler.py
