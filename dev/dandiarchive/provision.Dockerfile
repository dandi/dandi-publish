FROM python:3.6

WORKDIR /home

RUN git clone https://github.com/dandi/dandiarchive

RUN pip install girder-client

RUN mv /home/dandiarchive/docker/data /data
RUN mv /home/dandiarchive/docker/provision provision

ENTRYPOINT ["/home/provision/provision_entrypoint.sh"]
