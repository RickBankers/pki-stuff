#!/bin/bash
docker-build -t jenkinsansible-docker
docker run -d -p 2222:22 -v ~/jenkins:/home/jenkins -v /var/run/docker.sock:/var/run/docker.sock jenkinsansible