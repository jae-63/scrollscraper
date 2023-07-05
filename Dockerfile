# Set the base image to Ubuntu
FROM ubuntu:14.04

# File Author / Maintainer
MAINTAINER Jonathan Epstein <jonathanepstein9@gmail.com>

# Update the repository sources list
RUN apt-get update

# Install compiler and perl stuff
RUN apt-get install --yes \
 build-essential \
 gcc-multilib \
 apt-utils \
 perl \
 expat \
 libexpat-dev

# Install perl modules
RUN apt-get install -y cpanminus

RUN cpanm CPAN::Meta \
 readline \
 Term::ReadKey \
 YAML \
 Digest::SHA \
 Module::Build \
 ExtUtils::MakeMaker \
 LWP::Simple

RUN apt-get install --yes \
 libarchive-zip-perl

# Install GD
RUN apt-get remove --yes libgd-gd2-perl

RUN apt-get install --yes \
 libgd2-noxpm-dev

RUN cpanm GD


# Copy-hacked from tomersha/docker-ubuntu-14.04-python-3.6.2
# PyEnv
ENV PYENV_ROOT /root/.pyenv
ENV PATH $PYENV_ROOT/shims:$PYENV_ROOT/bin:$PATH
# Configure Python not to try to write .pyc files on the import of source modules
ENV PYTHONDONTWRITEBYTECODE true
ENV PYTHON_VERSION 3.6.2

RUN sudo apt-get update -q \
    && sudo apt-get install -y --no-install-recommends \
        build-essential \
        ca-certificates \
        curl \
        git \
        libbz2-dev \
        libreadline-dev \
        libsqlite3-dev \
        libssl-dev \
        zlib1g-dev

# Install pyenv and default python version
RUN git clone https://github.com/yyuu/pyenv.git /root/.pyenv \
    && cd /root/.pyenv \
    && git checkout `git describe --abbrev=0 --tags` \
    && sudo echo 'export PATH="$HOME/.pyenv/bin:$PATH"' >> ~/.bashrc \
    && sudo echo 'eval "$(pyenv init -)"'               >> ~/.bashrc

RUN pyenv install $PYTHON_VERSION
RUN pyenv local $PYTHON_VERSION

# Text-to-speech for ScrollScraper's buildmp3.cgi
RUN pip install gTTS


# Google Drive downloader for some large files which don't fit in free Github
RUN pip install gdown

WORKDIR /var/opt
RUN mkdir scrollscraper
RUN mkdir scrollscraper/webmedia
RUN mkdir scrollscraper/ScrollScraperalphaPNGs
ADD data/webmedia.tgz /var/opt/scrollscraper/webmedia
COPY ScrollScraperalphaPNGs/* /var/opt/scrollscraper/ScrollScraperalphaPNGs
ADD utilities/gifETL.pl /var/opt/scrollscraper/utilities
ADD *.cgi /var/opt/scrollscraper
ADD *.html /var/opt/scrollscraper
ADD *.txt /var/opt/scrollscraper
ADD *.gif /var/opt/scrollscraper
ADD *.GIF /var/opt/scrollscraper
