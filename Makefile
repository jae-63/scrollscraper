etl: build
	docker run -t scrollscraper -e "perl utilities/runETL.pl"

dataprep: build

build:
	docker build -t scrollscraper .
