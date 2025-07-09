#CONTAINER_ENGINE ?= docker
CONTAINER_ENGINE ?= podman
VERSION ?= 3.2.3
NOW_DATE := $(shell date '+%Y%m%d')

PLATFORM ?= linux/amd64
DOCKERFILE ?= Dockerfile

IMG ?= docker.io/ruo91/haproxy:$(VERSION)-$(NOW_DATE)

build:
	${CONTAINER_ENGINE} buildx build --platform="${PLATFORM}" -t ${IMG} -f ${DOCKERFILE} .

push:
	${CONTAINER_ENGINE} push ${IMG}

rm:
	${CONTAINER_ENGINE} rmi ${IMG}
