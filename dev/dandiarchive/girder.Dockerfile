FROM girder/girder:latest-py3

WORKDIR /home

RUN git clone https://github.com/dandi/dandiarchive

RUN pip install -e /home/dandiarchive/girder-dandi-archive && girder build

ENTRYPOINT ["/home/dandiarchive/docker/provision/girder_entrypoint.sh"]
