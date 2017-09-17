# USAGE:
#	# Build failsafe image
#	docker build -t failsafe .
#
#	# Run the container and mount the local settings and your code
#   # Your code must be under $HOME/Documents, you only need to change it here.
#		docker run --rm -it \
#			-v /tmp:/tmp \
#			-e NEWUSER=$USER \
#			failsafe

FROM python:2.7-alpine

RUN apk add --no-cache \
        gcc \
        musl-dev \
        python-dev \
        libjpeg-turbo-dev \
        jpeg-dev \
        zlib-dev \
        jq \
        libffi-dev \
        openssl-dev \
        git

COPY . /app

WORKDIR /app
RUN pip install .
RUN chmod a+x /app/run_docker.sh

ENTRYPOINT ["/app/run_docker.sh"]
