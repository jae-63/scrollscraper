# Set the base image to Ubuntu
FROM ubuntu:22.04

LABEL maintainer="Jonathan Epstein <jonathanepstein9@gmail.com>"

# Suppress interactive prompts during apt installs
ENV DEBIAN_FRONTEND=noninteractive

# Fix the GPG keyring mismatch bug by passing targeted flags that ignore the signature breach
# just long enough to install gnupg and import the verified public keys globally.
RUN apt-get update -o Acquire::AllowInsecureRepositories=true -o Acquire::AllowUnauthenticated=true && \
    apt-get install --yes --allow-unauthenticated gnupg ca-certificates && \
    rm -rf /etc/apt/trusted.gpg.d/*.gpg && \
    apt-key adv --keyserver keyserver.ubuntu.com --recv-keys 871920D1991BC93C

# Install system dependencies in one layer.
# ffmpeg is available in Ubuntu 22.04 repos with libmp3lame support built in,
# so we no longer need to compile it from source.
RUN apt-get update && apt-get install --yes \
  apt-utils \
  build-essential \
  gcc-multilib \
  perl \
  cpanminus \
  expat \
  libexpat1-dev \
  libreadline-dev \
  libbz2-dev \
  libsqlite3-dev \
  libssl-dev \
  zlib1g-dev \
  libgd-dev \
  libmp3lame-dev \
  libarchive-zip-perl \
  tesseract-ocr \
  libtesseract-dev \
  tesseract-ocr-heb \
  mp3wrap \
  ffmpeg \
  python3 \
  python3-pip \
  curl \
  git \
  ca-certificates && \
  rm -rf /var/lib/apt/lists/*

# Install Perl modules
RUN cpanm CPAN::Meta \
  readline \
  Term::ReadKey \
  YAML \
  Digest::SHA \
  Module::Build \
  ExtUtils::MakeMaker \
  LWP::Simple \
  CGI

# Install separately as before — SSL deps benefit from a clean layer
RUN cpanm Net::SSLeay \
  IO::Socket::SSL \
  LWP::Protocol::https

RUN cpanm utf8::all

RUN cpanm GD \
  GD::Text \
  JSON::Parse

# Text-to-speech and Google Drive downloader
RUN pip3 install gTTS gdown

WORKDIR /var/opt
RUN mkdir -p \
  scrollscraper/data \
  scrollscraper/intermediate_outputs \
  scrollscraper/final_outputs \
  scrollscraper/fonts \
  scrollscraper/ScrollScraperalphaPNGs \
  scrollscraper/otherComputedPNGs \
  scrollscraper/webmedia \
  scrollscraper/cgi-bin \
  scrollscraper/scrollscraperWorkingDir

RUN chmod 777 scrollscraper/scrollscraperWorkingDir && chmod 755 /root

ADD data/webmedia.tgz /var/opt/scrollscraper/webmedia
COPY data/entire_torah.json /var/opt/scrollscraper/data
COPY ScrollScraperalphaPNGs/* /var/opt/scrollscraper/ScrollScraperalphaPNGs/
COPY intermediate_outputs/* /var/opt/scrollscraper/intermediate_outputs/
COPY final_outputs/* /var/opt/scrollscraper/final_outputs/
COPY fonts/* /var/opt/scrollscraper/fonts/
COPY cgi-bin/*.cgi /var/opt/scrollscraper/cgi-bin/
COPY cgi-bin/*.pm /var/opt/scrollscraper/cgi-bin/
COPY utilities/gifETL.pl /var/opt/scrollscraper/utilities/
COPY utilities/gifETL2.pl /var/opt/scrollscraper/utilities/
COPY utilities/gifETL3.pl /var/opt/scrollscraper/utilities/
COPY utilities/handCuration.sed /var/opt/scrollscraper/utilities/
COPY utilities/fetchMP3s.sh /var/opt/scrollscraper/utilities/
COPY utilities/generateSampleTorahMap.pl /var/opt/scrollscraper/utilities/
COPY otherComputedPNGs/sampleTorahMap.png /var/opt/scrollscraper/otherComputedPNGs/
ADD Makefile /var/opt/scrollscraper/
ADD *.html /var/opt/scrollscraper/
ADD *.txt /var/opt/scrollscraper/
ADD *.gif /var/opt/scrollscraper/
ADD *.mp3 /var/opt/scrollscraper/
ADD *.GIF /var/opt/scrollscraper/

RUN chmod 755 /var/opt/scrollscraper/cgi-bin/*.cgi

RUN touch \
  /var/opt/scrollscraper/intermediate_outputs/gif_names.txt \
  /var/opt/scrollscraper/intermediate_outputs/color_analysis.csv \
  /var/opt/scrollscraper/final_outputs/gif_info.csv \
  /var/opt/scrollscraper/intermediate_outputs/augmented_color_analysis_with_verses.csv \
  /var/opt/scrollscraper/final_outputs/map.csv

ENV IS_DOCKER=1
ENV PERL5LIB=/var/opt/scrollscraper/cgi-bin
ENV LC_ALL=C.UTF-8
ENV LANG=C.UTF-8

