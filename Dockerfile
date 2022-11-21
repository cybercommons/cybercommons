ARG DOCKER_PYTHON_VERSION=3.9-slim-bullseye 
FROM python:$DOCKER_PYTHON_VERSION

ARG UNAME=apiuser
ARG UID=1000
ARG GID=1000

ENV LANG=C.UTF-8 LC_ALL=C.UTF-8 PYTHONUNBUFFERED=1

WORKDIR /
COPY requirements.txt ./
RUN python -m pip install --no-cache-dir --upgrade pip \
  && python -m pip install --no-cache-dir -r requirements.txt \
  && rm requirements.txt

COPY . /app
WORKDIR /app

#Setup API User
RUN groupadd -g $GID -o $UNAME \
  &&  useradd -m -u $UID -g $GID -o -s /bin/bash $UNAME \
  && chown $UNAME:$UNAME -R /app

USER $UNAME

EXPOSE 8080
CMD ["gunicorn", "--config=gunicorn.py", "api.wsgi:application"]
