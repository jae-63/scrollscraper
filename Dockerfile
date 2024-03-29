# Set the base image to Ubuntu
FROM ubuntu:14.04

# File Author / Maintainer
MAINTAINER Jonathan Epstein <jonathanepstein9@gmail.com>

# This project is constrained to use the Perl 'GD' module.   It also
# needs a simple Text-to-Speech command-line tool, for which Google's
# "gtts" is a good option.   Unfortanately at present these two requirements
# tie us to older versions of Ubuntu, Perl and Python than one would prefer.

# Update the repository sources list
RUN apt-get update

# Install compiler and perl stuff
RUN apt-get install --yes \
 build-essential \
 gcc-multilib \
 apt-utils \
 perl \
 expat \
 libexpat-dev \
 tesseract-ocr \
 libtesseract-dev \
 tesseract-ocr-heb \
 mp3wrap

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
 libssl-dev \
 zlib1g-dev

# for some reason we can't install this at the same time as the other modules
RUN cpanm Net::SSLeay \
 IO::Socket::SSL \
 LWP::Protocol::https

RUN apt-get install --yes \
 libarchive-zip-perl

# Install GD
RUN apt-get remove --yes libgd-gd2-perl

RUN apt-get install --yes \
 libgd2-noxpm-dev

RUN cpanm GD \
 GD::Text \
 JSON::Parse

RUN apt-get install --yes \
 libmp3lame-dev

RUN mkdir ffmpeg-source && \
  cd ffmpeg-source && \
  curl -k -o ffmpeg.tar.gz https://ffmpeg.org/releases/ffmpeg-6.0.tar.gz && \
  tar xzf ffmpeg.tar.gz && \
  cd ffmpeg-6.0/ && \
  ./configure --disable-x86asm --enable-libmp3lame && \
  make && \
  cp ffmpeg /usr/local/bin


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
RUN mkdir scrollscraper/data
RUN mkdir scrollscraper/intermediate_outputs
RUN mkdir scrollscraper/final_outputs
RUN mkdir scrollscraper/fonts
RUN mkdir scrollscraper/ScrollScraperalphaPNGs
RUN mkdir scrollscraper/otherComputedPNGs
RUN mkdir scrollscraper/webmedia
RUN mkdir scrollscraper/cgi-bin
ADD data/webmedia.tgz /var/opt/scrollscraper/webmedia
COPY data/entire_torah.json /var/opt/scrollscraper/data
COPY ScrollScraperalphaPNGs/* /var/opt/scrollscraper/ScrollScraperalphaPNGs
COPY intermediate_outputs/* /var/opt/scrollscraper/intermediate_outputs
COPY final_outputs/* /var/opt/scrollscraper/final_outputs
COPY fonts/* /var/opt/scrollscraper/fonts
COPY cgi-bin/*.cgi /var/opt/scrollscraper/cgi-bin
COPY cgi-bin/*.pm /var/opt/scrollscraper/cgi-bin
COPY utilities/gifETL.pl /var/opt/scrollscraper/utilities/
COPY utilities/gifETL2.pl /var/opt/scrollscraper/utilities/
COPY utilities/gifETL3.pl /var/opt/scrollscraper/utilities/
COPY utilities/handCuration.sed /var/opt/scrollscraper/utilities/
COPY utilities/fetchMP3s.sh /var/opt/scrollscraper/utilities/
COPY utilities/generateSampleTorahMap.pl /var/opt/scrollscraper/utilities/
COPY otherComputedPNGs/sampleTorahMap.png /var/opt/scrollscraper/otherComputedPNGs/
ADD Makefile /var/opt/scrollscraper
ADD *.html /var/opt/scrollscraper
ADD *.pm /var/opt/scrollscraper
ADD *.txt /var/opt/scrollscraper
ADD *.gif /var/opt/scrollscraper
ADD *.mp3 /var/opt/scrollscraper
ADD *.GIF /var/opt/scrollscraper
RUN chmod 755 /var/opt/scrollscraper/cgi-bin/*.cgi
RUN touch /var/opt/scrollscraper/intermediate_outputs/gif_names.txt
RUN touch /var/opt/scrollscraper/intermediate_outputs/color_analysis.csv
RUN touch /var/opt/scrollscraper/final_outputs/gif_info.csv
RUN touch /var/opt/scrollscraper/intermediate_outputs/augmented_color_analysis_with_verses.csv
RUN touch /var/opt/scrollscraper/final_outputs/map.csv
ENV IS_DOCKER=1
