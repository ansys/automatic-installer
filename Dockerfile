from python:3.7.13
COPY downloader_backend.py /run/
COPY requirements.txt /run/
COPY iss_templates.py /run/
COPY sharepoint/* /run/
RUN mkdir /settings
RUN python -m pip install -r /run/requirements.txt
ENTRYPOINT ["python", "/run/scheduler.py"]
