FROM python:3.7.9-alpine3.12
RUN apk add --no-cache --update git=2.26.2-r0 gcc=9.3.0-r2 musl-dev=1.1.24-r10 libffi-dev=3.3-r2 g++=9.3.0-r2 \
    # CVE-2020-28928 https://www.openwall.com/lists/musl/2020/11/19/1
    musl-utils=1.1.24-r10 \
    # something something default openssl on alpine not compatible with discord
    openssl=1.1.1g-r0 \
    && addgroup -g 1000 aoc \
    && adduser -u 1000 -H -D -G aoc -s /bin/sh aoc
COPY ["requirements.txt", "./"]
RUN pip3 install -r requirements.txt
WORKDIR /bot
USER aoc
COPY [".", "./"]
CMD ["python3", "main.py"]