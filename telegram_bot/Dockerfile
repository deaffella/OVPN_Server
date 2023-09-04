FROM python:3.9-bullseye

# set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

RUN pip3 install --upgrade pip
RUN pip3 install --no-cache-dir python-dotenv
RUN pip3 install --no-cache-dir python-telegram-bot
RUN pip3 install --no-cache-dir requests



WORKDIR /telegram_bot
RUN ln -sf /proc/1/fd/1 /var/log/test.log
CMD ["bash"]


