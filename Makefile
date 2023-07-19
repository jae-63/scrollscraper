BUILDSTAMP_FILE = docker-buildstamp
IMAGE = scrollscraper

.PHONY: all
all: $(BUILDSTAMP_FILE)

etl: $(BUILDSTAMP_FILE)
	docker run -t $(IMAGE) -e "perl utilities/runETL.pl"

dataprep: build

$(BUILDSTAMP_FILE): Dockerfile scrollscraper.cgi
	docker build -t $(IMAGE) .
	touch $@

clean:
	docker image rm -f $(IMAGE)
	rm -f $(BUILDSTAMP_FILE)


#======== Makefile targets to be run within the scrollscraper container appear below ==========

intermediate_outputs/gif_names.txt:
	find webmedia/ -name \*.gif | sort | sed "s/^/\//" >$@

final_outputs/gif_info.csv: intermediate_outputs/gif_names.txt
	@echo This command could take 5 minutes or so to run.  Be patient.
	perl utilities/gifETL.pl <$< >$@

intermediate_outputs/color_analysis.csv: intermediate_outputs/gif_names.txt
	@echo This command could take 8 minutes or so to run.  Be patient.
	perl utilities/gifETL2.pl <$< >$@

intermediate_outputs/augmented_color_analysis_with_verses.csv: intermediate_outputs/color_analysis.csv final_outputs/gif_info.csv
	grep -v BOOK,CHAPTER <$< | perl utilities/gifETL3.pl >$@

final_outputs/map.csv: intermediate_outputs/augmented_color_analysis_with_verses.csv utilities/handCuration.sed
	sed -f utilities/handCuration.sed <$< >$@

clean-scrollscraper-data:
	rm -f intermediate_outputs/* final_outputs/*

otherComputedPNGs/sampleTorahMap.png: utilities/generateSampleTorahMap.pl final_outputs/map.csv
	grep t2/1601C101.gif final_outputs/map.csv |  perl utilities/generateSampleTorahMap.pl >$@

test-scrollscraper.html: final_outputs/map.csv final_outputs/gif_info.csv
	perl scrollscraper.cgi "book=5&audioRepeatCount=1&coloring=0&doShading=on&startc=32&startv=35&endc=32&endv=45&dontUseCache=1&trueTypeFonts=1" >$@
