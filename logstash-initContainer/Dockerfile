FROM python:3-alpine AS builder

ENV ENV=dev

WORKDIR /data

COPY values_${ENV}.yml /values_${ENV}.yml
COPY requirements.txt /requirements.txt
COPY generate_pipelines.py /generate_pipelines.py
COPY templates /templates

RUN pip install -r requirements.txt

RUN python generate_pipelines.py

FROM alpine:3

WORKDIR /data

COPY --from=builder /data/generated /data/generated
COPY static_files /