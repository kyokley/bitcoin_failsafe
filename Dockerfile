FROM python:2.7-alpine

RUN apk add --no-cache \
        gcc \
        musl-dev \
        python-dev \
        libjpeg-turbo-dev \
        jpeg-dev \
        zlib-dev \
        jq \
        git

COPY . /app

WORKDIR /app
RUN pip install .

CMD ["failsafe"]
