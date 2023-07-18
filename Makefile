BUILDSTAMP_FILE = docker-buildstamp
IMAGE = scrollscraper

.PHONY: all
all: $(BUILDSTAMP_FILE)

etl: $(BUILDSTAMP_FILE)
	docker run -t $(IMAGE) -e "perl utilities/runETL.pl"

dataprep: build

$(BUILDSTAMP_FILE):
	docker build -t $(IMAGE) .
	touch $@

clean:
	docker image rm -f $(IMAGE)
	rm -f $(BUILDSTAMP_FILE)


======== Makefile targets to be run within the scrollscraper container appear below ==========

intermediate_outputs/gif_names.txt:
	find webmedia/ -name \*.gif | sort | sed "s/^/\//" >@$
