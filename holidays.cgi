#!/usr/bin/perl

use strict;
use LWP::Simple;
use HTML::TokeParser;
use CGI;

my $hebcalbase = "http://www.hebcal.com/holidays";
my $scrollscraperbase = "http://scrollscraper.adatshalom.net";

my $q = new CGI;
my $name;
if ($q->param('name')) {
	print "Content-type: text/html\n\n";
	$name = $q->param('name');
} else {
	$name = shift or die "Missing param";
}

die "Invalid parameter" unless $name =~ /^[-\w]{1,30}$/;

print "The content below has been derived from Hebcal.com, and the links have been modified to point to the ScrollScraper tikkun readings.\n";
print "The unadulterated version of this web page appears <a href=\"";
	
if ($name eq "MASTER") {
	my $url = "$hebcalbase";

	print "$url\">here</a>.<hr>\n";
	my $content = get($url) or die "Unable to fetch $url";
	my @lines = split /[\r\n]+/,$content;

	foreach (@lines) {
		chomp;
		if (/^(<dt>.*href=\")(.*)(\.html)(\".*)/) {
			print "$1$scrollscraperbase/holidays.cgi?name=$2$4\n";
		} elsif (/^(<tr><td>.*href=\")(.*)(\.html)?(\".*)/) {
			print "$1$scrollscraperbase/holidays.cgi?name=$2$4\n";
		} else {
			print "$_\n";
		}
	}
} else {
	my $url = "$hebcalbase/$name.html";

	print "$url\">here</a>.<hr>\n";
	my $content = get($url) or die "Unable to fetch $url";
	my @lines = split /[\r\n]+/,$content;

	foreach (@lines) {
		chomp;
		if (/^(.*title=\")(Audio from ORT\")/) {
			print "$1Tikkun text from ScrollScraper\"\n";
		} elsif (/^(.*title=\")(Hebrew-English bible text\")/) {
			print "$1Tikkun text from ScrollScraper\"\n";
		} elsif (/^(.*title=\")(Hebrew text and audio from ORT\")/) {
			print "$1Tikkun text and audio from ScrollScraper\"\n";
		} elsif (/(^.*href=\")([^\"\/]+)\.html(\".*$)/) {
			print "$1$scrollscraperbase/holidays.cgi?name=$2$3\n";
		} elsif (/^href=\"http.*bible.ort.org.*book=(\d)(.*\">)(\S+ )?([0-9\:\-]*)(.*)/ || /^href=\"http.*www.mechon-mamre.org\/p\/pt\/pt0(\d)(.*\">)(\S+ )?([0-9\:\-]*)(.*)/) {
			my $book = $1;
			my $optionalBookTitle = $3;
			my $range = $4;
			my $br = "<br>" if ($5 =~ /<br>/);
			my ($startc,$startv,$endc,$endv);
			if ($range =~ /^(\d+):(\d+)-(\d+):(\d+)/) {
				$startc = $1;
				$startv = $2;
				$endc = $3;
				$endv = $4;
			} elsif ($range =~ /^(\d+):(\d+)-(\d+)/) {
				$startc = $1;
				$startv = $2;
				$endc = $startc;
				$endv = $3;
			}
			if ($startc) {
				print "href=\"$scrollscraperbase/scrollscraper.cgi?doShading=1&book=$book&startc=$startc&endc=$endc&startv=$startv&endv=$endv\">$optionalBookTitle$range</a>$br\n";
			} else {
				print "$_\n";
			}
		} else {
			print "$_\n";
		}
	}
}
