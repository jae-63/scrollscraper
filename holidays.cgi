#!/usr/bin/perl

use strict;
use LWP::Simple;
use HTML::TokeParser;
use CGI;

binmode( STDOUT, "encoding(UTF-8)" );

my $hebcalbase = "https://www.hebcal.com/holidays";
my $scrollscraperbase = "https://scrollscraper.adatshalom.net";

my @englishBookNames =
  ( "Genesis", "Exodus", "Leviticus", "Numbers", "Deuteronomy" );

my %englishBookName2Number;

my $book = 1;
foreach my $bookName (@englishBookNames) {
     $englishBookName2Number{$bookName} = $book++;
}


my $q = new CGI;
my $name;
if ($q->param('name')) {
	print "Content-type: text/html\n\n";
	$name = $q->param('name');
} else {
	$name = shift or die "Missing param";
}

die "Invalid parameter" unless $name =~ /^[-\w]{1,30}$/;

my $agent = LWP::UserAgent->new;

$agent->ssl_opts(verify_hostname => 0,
              SSL_verify_mode => 0x00);
my $content;

print "The content below has been derived from Hebcal.com, and the links have been modified to point to the ScrollScraper tikkun readings.\n";
print "The unadulterated version of this web page appears <a href=\"";
	
if ($name eq "MASTER") {
	my $url = "$hebcalbase";

	print "$url\">here</a>.<hr>\n";
        my $response = $agent->get($url) or die "Unable to fetch $url";

        $content = $response->decoded_content;
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
	my $url = "$hebcalbase/$name";

	print "$url\">here</a>.<hr>\n";
        my $response = $agent->get($url) or die "Unable to fetch $url";

        $content = $response->decoded_content;
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
		} elsif (/(.*)<a title="[^"]*".* href=\"https:\/\/www.sefaria.org\/(Genesis|Exodus|Leviticus|Numbers|Deuteronomy)\.(\d+)\.(\d+)-(\d+\.)?(\d+).*<\/a>(.*)/) {
			my $prefix = $1;
			my $suffix = $7;
			my $bookTitle = $2;
			my $book = $englishBookName2Number{$bookTitle};
			my ($startc,$startv,$endc,$endv);
			$startc = $3;
			$startv = $4;
			$endc = $5 || $startc;
			$endv = $6;
			my $range = "$startc:$startv-$endc:$endv";
			if ($startc) {
				print "${prefix}<a title=\"Tikkun text from ScrollScraper\" href=\"$scrollscraperbase/scrollscraper.cgi?doShading=1&book=$book&startc=$startc&endc=$endc&startv=$startv&endv=$endv\">$bookTitle $range</a>${suffix}\n";
			} else {
				print "$_\n";
			}
		} else {
			print "$_\n";
		}
	}
}
