FROM kylemanna/openvpn


# set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

RUN apk add python3
RUN apk add tzdata
RUN python3 -m ensurepip


# install dependencies
RUN pip3 install --upgrade pip
COPY requirements.txt /opt/requirements.txt
RUN pip3 install -r /opt/requirements.txt


COPY . /server_management
WORKDIR /server_management

RUN ln -sf /proc/1/fd/1 /var/log/test.log
CMD ["bash"]