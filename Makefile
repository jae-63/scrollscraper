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


#======== Makefile targets to be run within the scrollscraper container appear below ==========

intermediate_outputs/gif_names.txt:
	find webmedia/ -name \*.gif | sort | sed "s/^/\//" >$@

final_outputs/gif_info.csv: intermediate_outputs/gif_names.txt
	@echo This command could take 10 minutes or so to run.  Be patient.
	perl utilities/gifETL.pl <$< >$@

intermediate_outputs/color_analysis.csv: intermediate_outputs/gif_names.txt
	@echo This command could take 30 minutes or so to run.  Be patient.
	perl utilities/gifETL2.pl <$< >$@

intermediate_outputs/augmented_color_analysis_with_verses.csv: intermediate_outputs/color_analysis.csv final_outputs/gif_info.csv
	grep -v BOOK,CHAPTER <$< | perl utilities/gifETL3.pl >$@

final_outputs/map.csv: intermediate_outputs/augmented_color_analysis_with_verses.csv utilities/handCuration.sed
	sed -f utilities/handCuration.sed <$< >$@
