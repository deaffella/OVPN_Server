FROM kylemanna/openvpn


# set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

RUN apk add python3
RUN python3 -m ensurepip


# install dependencies
RUN pip3 install --upgrade pip
RUN pip3 install --no-cache-dir fastapi uvicorn
RUN pip3 install --no-cache-dir pymongo
RUN pip3 install --no-cache-dir motor

COPY fastapi /fastapi
WORKDIR /fastapi

RUN ln -sf /proc/1/fd/1 /var/log/test.log
CMD ["bash"]