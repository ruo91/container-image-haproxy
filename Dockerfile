#### Step 1. Build ####
FROM registry.fedoraproject.org/fedora:43 as builder
LABEL maintainer="Yongbok Kim (ruo91@yongbok.net)"
LABEL source="https://github.com/ruo91/container-image-haproxy"
ARG TARGETARCH

# Global Variable
WORKDIR /opt
ENV PREFIX_DIR /opt/haproxy

# ADD Group & User
ENV HAPROXY_UID=1000
ENV HAPROXY_GID=1000
RUN groupadd -g $HAPROXY_GID haproxy \
 && useradd -d $PREFIX_DIR -c "HAProxy User" -u $HAPROXY_UID -g $HAPROXY_GID -s /sbin/nologin haproxy

# Package
ENV GPGCHECK=0
RUN dnf install -y @development-tools \
 && dnf install -y make systemd-devel git-core procps-ng openssl openssl-devel pcre2-devel zlib-devel libslz-devel

# HAProxy Download
ENV HAPROXY_MAJOR_VER=3.3
ENV HAPROXY_VER=haproxy-3.3.1
RUN curl -o "$HAPROXY_VER.tar.gz" -L "https://www.haproxy.org/download/$HAPROXY_MAJOR_VER/src/$HAPROXY_VER.tar.gz" \
 && tar xzvf $HAPROXY_VER.tar.gz && rm -f $HAPROXY_VER.tar.gz

# Build Settings
COPY conf/use-flags.txt $HAPROXY_VER/use-flags.txt
RUN cd $HAPROXY_VER \
 && sed -i -f use-flags.txt Makefile \
 && sed -i "/^PREFIX =/ s:.*:PREFIX = ${PREFIX_DIR}:" Makefile \
 && sed -i '/^TARGET =/ s:.*:TARGET = linux-glibc:' Makefile \
 && make -j $(nproc) && make install

#### Step 2. Main ####
FROM registry.fedoraproject.org/fedora:43
LABEL maintainer="Yongbok Kim (ruo91@yongbok.net)"
LABEL source="https://github.com/ruo91/container-image-haproxy"
ARG TARGETARCH

# Global Variable
WORKDIR /opt
ENV PREFIX_DIR /opt/haproxy

# ADD Group & User
ENV HAPROXY_UID=1000
ENV HAPROXY_GID=1000
RUN groupadd -g $HAPROXY_GID haproxy \
 && useradd -d $PREFIX_DIR -c "HAProxy User" -u $HAPROXY_UID -g $HAPROXY_GID -s /sbin/nologin haproxy

# Package
ENV GPGCHECK=0
RUN dnf install -y procps-ng openssl openssl-devel pcre2-devel zlib-devel tzdata \
    libslz-devel python3-jinja2 iputils net-tools bind-utils iproute ncurses htop \
    tcpdump wireshark-cli numactl numactl-libs

# Copy
COPY --from=builder ${PREFIX_DIR}/sbin/haproxy /usr/sbin/haproxy

# Init
COPY conf/entrypoint.sh ${PREFIX_DIR}/entrypoint.sh
COPY conf/generate.py ${PREFIX_DIR}/generate.py
COPY conf/haproxy-template.cfg ${PREFIX_DIR}/haproxy-template.cfg
RUN mkdir ${PREFIX_DIR}/run && chown -R $HAPROXY_UID:$HAPROXY_GID ${PREFIX_DIR}/*

# Time Zone
ENV TZ=Asia/Seoul

# Switch User
USER 1000

# HAProxy Ports
EXPOSE 1936/tcp 8080/tcp 8443/tcp

# HAProxy Starting
ENTRYPOINT ["/opt/haproxy/entrypoint.sh"]
CMD ["/usr/sbin/haproxy", "-f", "/opt/haproxy/haproxy.cfg"]
