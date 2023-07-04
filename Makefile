etl: build
	docker run -t scrollscraper utilities/runETL.pl -v ../bigdata:bigdata

dataprep: build

build:
	docker build -t scrollscraper .
