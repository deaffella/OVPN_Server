FROM python:3.11-bullseye
MAINTAINER Letenkov Maksim <letenkovmaksim@yandex.ru>

# set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

RUN apt update && \
    apt install -y \
        locales locales-all \
        build-essential pkg-config gcc \
        nano \
        python3-pip \
     && \
    apt autoremove -y && \
    apt autoclean && \
    apt clean

COPY requirements.txt /opt/requirements.txt
RUN python3 -m pip install --upgrade pip
RUN pip3 install --no-cache-dir -r /opt/requirements.txt

COPY . /fastapi
WORKDIR /fastapi


RUN ln -sf /proc/1/fd/1 /var/log/test.log
CMD ["bash"]