# Centos base image with tini as a init process
# see: https://github.com/krallin/tini
FROM krallin/centos-tini:7

WORKDIR /opt/test_user

# System dependencies
RUN yum -y install epel-release \
    && yum -y install \
              python-pip \
              python-devel \
              python36 \
              python36-devel \
              expat \
              zip \
              git \
              unzip \
              curl \
              bzip2 \
              freetype \
              libgfortran \
              libgomp \
              procps \
              zeromq-devel \
    && yum -y groupinstall "Development tools" \
    && yum -y autoremove \
    && yum clean all

# Python modules
COPY scripts ./scripts

# Install python dependencies
COPY requirements.txt ./requirements.txt

# Clone Distributed fork and checkout to debug branch
RUN git clone https://github.com/jjerphan/distributed.git && \
    cd distributed && \
    git checkout 1.28.0_debug && \
    git show --summary | cat && \
    cd ..

# Clone Joblib fork and checkout to debug branch
RUN git clone https://github.com/jjerphan/joblib.git && \
    cd joblib && \
    git checkout 0.13.2_debug && \
    git show --summary | cat && \
    cd ..

# Print the system python version
RUN python -c "import platform ; print(platform.sys.version)"

# Install dependencies
RUN pip install --upgrade pip
RUN pip install -r ./requirements.txt
RUN pip install Cython numpy
RUN pip install -e joblib
RUN pip install -e distributed

# To use an independently installed version of joblib instead
# of the vendored version.
ENV SKLEARN_SITE_JOBLIB=1

# Create user home dir and set permissions
WORKDIR /home/test_user

RUN groupadd -r test_user \
    && useradd -r -g test_user -d /home/test_user test_user \
    && chown -Rh test_user:test_user /home/test_user

USER test_user

# Add tini in entrypoint to used this as the init
# instead of docker's default init process for handling signal appropriately
ENTRYPOINT ["/usr/local/bin/tini", "--", "python", "-m", "script.entrypoint"]