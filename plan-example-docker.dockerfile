FROM ubuntu:16.04

RUN apt-get update && apt-get install sl

ENTRYPOINT /usr/games/sl