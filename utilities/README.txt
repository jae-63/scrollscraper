This directory contains some misc data and scripts.   In particular, it includes
some "ETL" scripts which process an one or more input datasets and produce a new 
dataset.

At present, here are the directory contents:
fetchMP3s.sh                   - a script which fetches large tarballs from the cloud which contain MP3 recordings.   These files are too large to fit into Github. 
generateAlphaPNGs.pl           - an older script which produces the ~890 "alpha" PNG files which are used for ScrollScraper shading
gifETL.pl                      - takes as input 'gif_names_from_cache_old.txt' and uses that list plus our knowledge of the ORT GIF file naming convention to produce a report of the form: "BOOK,CHAPTER,VERSE,FIRSTGIF,FINALGIF,LINENUMBERONWHICHTHISVERSEBEGINS,INDEXOFVERSESTARTPOSITIONONTHATLINE,STARTX,STARTY,ENDX,ENDY"
gifETL2.pl                     - also takes as input 'gif_names_from_cache_old.txt' but also performs image processing on all of the listed GIFs.    Produces a report which for each GIF row reports a list of the associated (startx,endx,color).    This script takes a long time to run, perhaps 20 minutes.
gifETL3.pl                     - consumes the output of gifETL2.pl and augments the (startx,endx,color) with two additional fields, yielding (startx,endx,color,chapter,verse).   Note that the Torah book number (1-5) is implicit on each line since the GIF directory/filename is included.   This logic could be refactored into gifETL2.pl
gifETL3.pl                     - Perform some rudimentary checking of the gifETL2 or gifETL3 output.   Trying to resolve missing space-sections in those outputs, and section-widths not adding up to the expected 445.
gif_names_from_cache_old.txt   - a list of all the right-side GIF files from bible.ort.org for the Torah.   Luckily we have copies of all of these files!
handCuration.sed               - some hand-curation which we might use to handle special cases without needing to manually modify either our ETL outputs or the Hebrew Torah text retrieved from Sefaria.  A sample case might include forcing subtle reformatting of the Shirat Hayam text in Exodus:15
hebrewTextETL.pl               - take an input JSON retrieved from a MongoDB database which Sefaria provides.   Convert that into a Perl script which represents all of the Hebrew text in the Torah.    This output has been slightly modified manually in the verse2hebrew.pm Perl Module which appears elsewhere in this code repository.
