from python:3.7.13-alpine
COPY code/* /run/
RUN mkdir /settings
RUN apk add build-base  # install gcc
RUN apk add libffi-dev
RUN apk add krb5
RUN python -m pip install -r /run/requirements.txt
RUN python /run/scheduler.py
