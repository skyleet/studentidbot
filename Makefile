.PHONY: build push

push: build
	docker push mapio/studentidbot:$(shell git rev-parse --short HEAD)
	docker tag mapio/studentidbot:$(shell git rev-parse --short HEAD) mapio/studentidbot:latest
	docker push mapio/studentidbot:latest

build:
	docker build -t mapio/studentidbot:$(shell git rev-parse --short HEAD) .

