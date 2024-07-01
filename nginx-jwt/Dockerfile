FROM nginxinc/nginx-unprivileged:1.25.3-alpine as builder

USER root

RUN apk add --no-cache \
    jq \
    gcc \
    libc-dev \
    make \
    openssl-dev \
    openssl \
    curl \
    jansson-dev \
    automake \
    libtool \
    cmake  \
    check-dev \
    autoconf 

# TODO ENABLE NA NASI SITI
# COPY apigw_jwks_to_pem.sh /etc/nginx/certs/apigw_jwks_to_pem.sh
# RUN sh /etc/nginx/certs/apigw_jwks_to_pem.sh
COPY test-apigw-default_ssl_key-public_key.pem /etc/nginx/certs/test-apigw-default_ssl_key-public_key.pem

ADD libjwt-1.17.1.tar.bz2 /

WORKDIR /libjwt-1.17.1

RUN autoreconf -i \
    && ./configure \
    && make all \
    && make check \
    && make install

FROM nginxinc/nginx-unprivileged:1.25.3-alpine

ENV NGINX_ENVSUBST_OUTPUT_DIR /etc/nginx
ENV NGINX_APIGW_PUBLIC_KEY=test-apigw-default_ssl_key-public_key.pem
ENV APMSERVER_REWRITE_PATH=/test/apm
ENV APMSERVER_PUBLIC_REWRITE_PATH=/test/public-apm
ENV APMSERVER_SERVICE=http://apm-server-main-apm-http.elk.svc.cluster.local:8200

COPY --from=builder /etc/nginx/certs /etc/nginx/certs
COPY --from=builder /usr/local/lib/libjwt.so.2.10.1 /lib

COPY ./nginx.conf.template /etc/nginx/templates/nginx.conf.template
COPY ngx_http_auth_jwt_module.so /etc/nginx/modules/ngx_http_auth_jwt_module.so

USER root

RUN apk add --no-cache jansson \
    && ln -s /lib/libjwt.so.2.10.1 /lib/libjwt.so.2 \
    && ln -s /lib/libjwt.so.2.10.1 /lib/libjwt.so.1 \
    && ln -s /lib/libjwt.so.2.10.1 /lib/libjwt.so

USER nginx