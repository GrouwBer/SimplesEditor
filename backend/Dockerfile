FROM ubuntu:24.04

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y --no-install-recommends \
      build-essential \
      nasm \
      binutils-i686-linux-gnu \
      python3 python3-venv python3-pip \
      ca-certificates curl \
    && rm -rf /var/lib/apt/lists/*

COPY ./simples-compiler /opt/simples-compiler
RUN cd /opt/simples-compiler && make && cp build/simplesc /usr/local/bin/simplesc

WORKDIR /app
COPY backend/requirements.txt .
RUN pip install --break-system-packages -r requirements.txt
COPY backend/ .

EXPOSE 5000
CMD ["gunicorn", "-k", "geventwebsocket.gunicorn.workers.GeventWebSocketWorker", \
     "-w", "4", "-b", "0.0.0.0:5000", "wsgi:app"]
