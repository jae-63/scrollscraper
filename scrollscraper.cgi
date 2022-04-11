#!/usr/bin/perl
#
# Copyright 2006-2009 by Jonathan Epstein (jonathan.epstein@adatshalom.net)
# 
# This program is free software; you can redistribute it and/or 
# modify it under the same terms as Perl itself.
# 
# See http://www.perl.com/perl/misc/Artistic.html
#
# The author wishes to thank the WorldORT organization for its wonderful 
# Navigating the Bible website (bible.ort.org), and will yield copyright
# to this software to WorldORT upon request.
#
# -----------------------------------------
#
# Fetch a Torah-reader's Tikkun excerpt from the bible.ort.org website.
# The resulting output is suitable for printing or for exporting to a
# handheld device.
#
use strict;
use LWP::Simple;
use HTML::TokeParser;
use GD;
use CGI;
 
# sample: https://bible.ort.org/books/torahd5.asp?action=displaypage&book=2&chapter=27&verse=1&portion=19

# 
# $outputVersion should be incremented each time the format is changed in
# a manner which affects previously cached output files
# 
my $outputVersion = 6;

my $site = "https://bible.ort.org";
my $outputSite = $site;
my $outputSite = "https://scrollscraper.adatshalom.net";
my $base = "$site/books/torahd5.asp?action=displaypage&book=%d&chapter=%d&verse=%d&portion=%d";
my $gifWidth = 445;
my $shadingDir = "ScrollScraperalphaPNGs";
my $forbiddenFile = "forbidden-referers.txt";
my $smilFormat = "<audio src=\"https://bible.ort.org/webmedia/t%d/%02d%02d.ra\" title=\"%s %d:%d\" %s/>";
my $mainURL = "http://scrollscraper.adatshalom.net";
my $fliteOptions = "--setf duration_stretch=1.2"; # slow down the audio by 20%
my $fliteSpeechSynthesis = "/home/jepstein/flite/flite-1.3-release/bin/flite";
my $festivalSpeechSynthesis = "/home/jepstein/festival/festival/bin/text2wave";
my $festivalOptions = "-scale 3 -o";
my $lame = "/home/jepstein/lame-3.97/frontend/lame"; # use "lame" for WAV->MP3 conversion

my $cachebase = "./cache/";
my $smilbase = "./smil/";

my $usage = "Usage: " . $0 . " book startchapter startverse endchapter endverse";
my $gifCount = 0;
my $book;
my $startc;
my $startv;
my $endc;
my $endv;
my $sbs = 1;
my $translit = 1;
my $showStartAndEndButtons = 0;
my $useCache = 1; # not part of "$flags" below
my $doAudio = 1;
my $audioRepeatCount = 1;
my $coloring;
my $generateCache = 1;
my $doShading = 0;
my $blankImage = "alpha_TOP1_0.png"; # used for padding on LHS of table, when $doShading is used

my $agent = LWP::UserAgent->new;

$agent->ssl_opts(verify_hostname => 0,
              SSL_verify_mode => 0x00);


my $q = new CGI;

if ($q->param('book')) {
	print "Content-type: text/html\n\n";

	foreach my $key ($q->param) {
		next if $key eq 'coloring';
		if ($q->param($key) !~ /^\d+$/ && $q->param($key) !~ /^(on|off)$/) {
			my $str = "Invalid parameter: $key=" . $q->param($key);
			print "$str\n";
			die "$str";
		}
	}

	$book = $q->param('book');
	$startc = $q->param('startc');
	$startv = $q->param('startv');
	$endc = $q->param('endc');
	$endv = $q->param('endv');
	$sbs = 1 if $q->param('sbs');
	$sbs = 0 if $q->param('col1');
	$translit = 0 if $q->param('notranslit');
	$showStartAndEndButtons = 1 if $q->param('showStartAndEndButtons');
	$useCache = 0 if $q->param('dontUseCache');
	$doAudio = 0 if $q->param('noAudio');
	$audioRepeatCount = $q->param('audioRepeatCount') if $q->param('audioRepeatCount');
	$coloring = $q->param('coloring') if $q->param('coloring');
	$doShading = $q->param('doShading') if $q->param('doShading');
	
	if (-f $forbiddenFile && defined $ENV{"HTTP_REFERER"}) {
		open FORB, "<$forbiddenFile";
		while (<FORB>) {
			chomp;
			if (/(.*)\t(.*)/) {
				my $pat = $1;
				my $msg = $2;
				$_ = $ENV{"HTTP_REFERER"};
				if (/$pat/) {
					print $msg;
					die "Illegal user: $_ $msg";
				}
			}
		}
		close FORB;
	}
} else {
	$book = shift or die $usage;
	$startc = shift or die $usage;
	$startv = shift or die $usage;
	$endc = shift or die $usage;
	$endv = shift or die $usage;
	$sbs = shift; # optional
	$useCache = 0; # JAE TEMP 07/30/09, for development only
	$doShading = 1; # more debugging code
}

my $flags = $sbs | ($translit << 1) | ($showStartAndEndButtons << 2) | ($doAudio << 3) | ($doShading << 4);
#$coloring = "25,25,112,25,25,112" if ($ENV{"HTTP_USER_AGENT"} =~ /NetFront.*Kindle/ && ! $coloring);
$coloring = "25,25,112,0,139,139" if ($ENV{"HTTP_USER_AGENT"} =~ /NetFront.*Kindle/ && ! $coloring); # modest shading for traditional greyscale Kindles
$useCache = 0 if $coloring;
$generateCache = 0 if $coloring;

my $audioList = "";

my @englishBookNames = ("Genesis","Exodus","Leviticus","Numbers","Deuteronomy");
#
# All Hebrew transliterations used here correspond to conventions used on ORT web site
#
my @hebrewBookNames = ("Bereshit","Shemot","VaYikra", "BeMidbar", "Devarim");

# book, start-chapter, start-verse, portion, title
my @parshaInfo = (
[1, 1, 1, 1, "Bereshit"],
[1, 6, 9, 2, "Noach"],
[1, 12, 1, 3, "Lech Lecha"],
[1, 18, 1, 4, "VaYera"],
[1, 23, 1, 5, "Chayey Sarah"],
[1, 25, 19, 6, "Toledot"],
[1, 28, 10, 7, "VaYetse"],
[1, 32, 4, 8, "VaYishlach"],
[1, 37, 1, 9, "VaYeshev"],
[1, 41, 1, 10, "MiKets"],
[1, 44, 18, 11, "VaYigash"],
[1, 47, 28, 12, "VaYechi"],
[2, 1, 1, 13, "Shemot"],
[2, 6, 2, 14, "VaEra"],
[2, 10, 1, 15, "Bo"],
[2, 13, 17, 16, "BeShalach"],
[2, 18, 1, 17, "Yitro"],
[2, 21, 1, 18, "Mishpatim"],
[2, 25, 1, 19, "Terumah"],
[2, 27, 20, 20, "Tetsaveh"],
[2, 30, 11, 21, "Ki Tisa"],
[2, 35, 1, 22, "VaYakhel"],
[2, 38, 21, 23, "Pekudey"],
[3, 1, 1, 24, "VaYikra"],
[3, 6, 1, 25, "Tsav"],
[3, 9, 1, 26, "Shemini"],
[3, 12, 1, 27, "Tazria"],
[3, 14, 1, 28, "Metsora"],
[3, 16, 1, 29, "Acharey Mot"],
[3, 19, 1, 30, "Kedoshim"],
[3, 21, 1, 31, "Emor"],
[3, 25, 1, 32, "BeHar"],
[3, 26, 3, 33, "BeChukotay"],
[4, 1, 1, 34, "BeMidbar"],
[4, 4, 21, 35, "Naso"],
[4, 8, 1, 36, "BeHa'alotecha"],
[4, 13, 1, 37, "Shlach"],
[4, 16, 1, 38, "Korach"],
[4, 19, 1, 39, "Chukat"],
[4, 22, 2, 40, "Balak"],
[4, 25, 10, 41, "Pinchas"],
[4, 30, 2, 42, "Matot"],
[4, 33, 1, 43, "Mas'ey"],
[5, 1, 1, 44, "Devarim"],
[5, 3, 23, 45, "VaEtchanan"],
[5, 7, 12, 46, "Ekev"],
[5, 11, 26, 47, "Re'eh"],
[5, 16, 18, 48, "Shoftim"],
[5, 21, 10, 49, "Ki Tetse"],
[5, 26, 1, 50, "Ki Tavo"],
[5, 29, 9, 51, "Nitsavim"],
[5, 31, 1, 52, "VaYelech"],
[5, 32, 1, 53, "Ha'azinu"],
[5, 33, 1, 54, "Vezot HaBerachah"],
);

# Derived from bible.ort.org.   Note that both the King James bible and Machon Mamre differ from this!
my @versesPerChapter = (
[31,25,24,26,32,22,24,22,29,32,32,20,18,24,21,17,27,33,38,18,34,24,20,67,34,35,46,22,35,43,54,33,20,31,29,43,36,30,23,23,57,38,34,34,28,34,31,22,33,26],
[22,25,22,31,23,30,29,28,35,29,10,51,22,31,27,36,16,27,25,23,37,30,33,18,40,37,21,43,46,38,18,35,23,35,35,38,29,31,43],
[17,16,17,35,26,23,38,36,24,20,47,8,59,57,33,34,16,30,37,27,24,33,44,23,55,46,34],
[54,34,51,49,31,27,89,26,23,36,35,16,33,45,41,35,28,32,22,29,35,41,30,25,18,65,23,31,39,17,54,42,56,29,34,13],
[46,37,29,49,30,25,26,20,29,22,32,31,19,29,23,22,20,22,21,20,23,29,26,22,19,19,26,69,28,20,30,52,29,12],
);



#
# the "left" and "right" nomenclature below refer to layout in a traditional
# tikkun, not how it appears on the ORT web pages
#
# i.e.: left  = like it appears in the Torah scroll
#       right = with vowels, punctuation + trop
#
my %seenLefts;
my %seenRights;
my %imagesInEnd;
my @leftOutputs;
my @rightOutputs;
my $url;
my $p;
my $portion;
my $content;
my $firstURL;
my $lastURL;
my $startTranslit1Color = "#009900";
my $startTranslit2Color = "#66ff99";
my $endTranslit1Color = "#ffff33";
my $endTranslit2Color = "#cc0000";
my $cacheOpenFailed = 0;
my $cacheOutRef;
my $smilFileName;

my $maxFetches = 200; # safety valve;

#
# N.B.: The ORT website is pretty fussy about portion numbers; it seems to require
# that URLs specify the correct portion for a given chapter&verse.  Therefore some care
# is required to submit valid URLs.
#
my $beginPortion = calcPortion($book,$startc,$startv);
my $chaptersInBook = $versesPerChapter[$book-1] + 1;

if ($doAudio && $endc >= $startc) {
	system("mkdir -p $smilbase");
	$smilFileName = rangeToFileName($smilbase, $book,$startc,$startv,$endc,$endv,$flags) . ".smil";
	open SMIL,">$smilFileName" or die "Unable to open $smilFileName for output";
	print SMIL "<smil xmlns=\"http://www.w3.org/2001/SMIL20/Language\">\n  <head>\n";

	if (-x $festivalSpeechSynthesis) {
#		my $tts = "This is an excerpt from parshat" . getPortionName($beginPortion) . ", " . getBookName($book) . ", Chapter $startc, ";
		my $tts = "This is an excerpt from " . getBookName($book) . ", Chapter $startc, "; # it would be nice to include the Parsha, but the pronounciation is too poor
		if ($startc != $endc) {
			$tts .= "verse $startv through chapter $endc verse $endv.";
		} else {
			$tts .= "verses $startv through $endv.";
		}

		$tts .= "  The following recorded materials are copyright world-ORT, 1997, all rights reserved.";
		my $wavFileName = rangeToFileName($smilbase, $book,$startc,$startv,$endc,$endv,$flags) . ".wav";
		my $audioFileName = rangeToFileName($smilbase, $book,$startc,$startv,$endc,$endv,$flags) . ".mp3";

		# note: if desired, we could run this TTS processing and audio conversion in the background
#		system ("$fliteSpeechSynthesis $fliteOptions \"$tts\" $wavFileName; $lame -h --silent --scale 2 $wavFileName $audioFileName; rm -f $wavFileName");
		system ("(/bin/echo \"$tts\" | $festivalSpeechSynthesis $festivalOptions $wavFileName; $lame -h --silent --scale 2 $wavFileName $audioFileName; rm -f $wavFileName) &");

		# trick from SMIL documentation; create a 1pixelx1pixel region so we can attach a volume-adjustment ("soundLevel") to it
		print SMIL "    <layout>\n      <root-layout height=\"1\" width=\"1\"/>\n";

		# crank up the volume for the synthesized speech, since natively it's much quieter than the ORT leyning recordings
		print SMIL "      <region id=\"highvolume\" soundLevel=\"300%\"/>\n    </layout>\n";

		print SMIL "  </head>\n  <body>\n";
		print SMIL "    <audio src=\"$mainURL/$audioFileName\"/>\n";
	} else {
		print SMIL "  </head>\n  <body>\n";
	}
	print SMIL "    <seq title=\"" . getBookName($book) . "$startc:$startv-$endc:$endv\"";
	print SMIL " repeat=\"$audioRepeatCount\"" if ($audioRepeatCount > 1);
	print SMIL ">\n";

	my $v = $startv;
	my $c = $startc;
	my $count = 0;
	$audioList = "";

	while ($count++ < $maxFetches) {
		my $extra = "";
		$extra = "begin=\"1.5s\"" if ($count <= 1);
		$audioList .= "," if ($count > 1);
		$audioList .= sprintf "%02d%02d",$c,$v;
		printf SMIL "      $smilFormat\n",$book,$c,$v,getBookName($book),$c,$v,$extra;
		last if ($c >= $endc && $v >= $endv);
		$v++;
		if ($v > $versesPerChapter[$book-1][$c-1]) {
			$v = 1;
			$c++;
			last if $c >= $chaptersInBook;
		}
	}
	print SMIL "    </seq>\n  </body>\n</smil>\n";
	close SMIL;
}



my $cacheFileName = rangeToFileName($cachebase, $book,$startc,$startv,$endc,$endv,$flags) . ".html";
if (CachedCopyIsValid($cacheFileName, $outputVersion) && $useCache) {
	if (open CACHEIN,"<$cacheFileName") {
		while(<CACHEIN>) {
			print $_;
		}
		close CACHEIN;
		exit 0;
	}
}

if ($generateCache && open CACHEOUT,">$cacheFileName") {
	$cacheOutRef = \*CACHEOUT;
} else {
	$cacheOutRef = \*STDOUT;
	$cacheOpenFailed = 1;
}


#
# lookup the ending verse; we'll use this information to determine when
# our forward-traversal through the ORT website is ready to stop
#
my $endPortion = calcPortion($book,$endc,$endv);
$url = sprintf($base,$book,$endc,$endv,$endPortion);
$lastURL = $url;

my $response = $agent->get($url) or die "Unable to fetch $url";

$content = $response->decoded_content;

my $lastTranslit = fetchTransliteration($content,$endc,$endv,1, $endTranslit1Color, $endTranslit2Color) if $translit;
my $firstTranslit;

#
# compute the verse following ($endc,$endv), with exceptions for the end of a book
# This is used to handle the case where a verse has not yet ended on the ORT page, so
# we need to include GIFs from the following ORT page as well.  Note that we don't
# attempt to handle the (unlikely) case where a verse spans 3 or more ORT pages.
#
my $endcFollow = $endc;
my $endvFollow = $endv + 1;
if ($endvFollow > $versesPerChapter[$book-1][$endc-1]) {
	$endvFollow = 1;
	$endcFollow++;
	if ($endvFollow >= $chaptersInBook) {
		$endcFollow = $endc;
		$endvFollow = $endv;
	}
}

$p = HTML::TokeParser->new(\$content);
while (my $token = $p->get_token()) {
	if ($token->[1] eq "img") {
		my $src = $token->[2]{"src"};
		if ($src =~ /^\/webmedia\/t\d\//) {
			$imagesInEnd{$src}++;
		}
	}
}


$url = sprintf($base,$book,$startc,$startv,$beginPortion);
$firstURL = $url;
my $done = 0;
my $almostdone = 999;
$portion = $beginPortion;

my $tableDepth = 0;
my @trCount;
my $lastRight;
my %verseInfo;
my %verseShades;

while ($maxFetches-- && !$done) {
	# pull out all Torah GIFs (right&left) & Forward link
	# for next $url, follow Forward link
	#
	# push previously unseen image links onto lists
	# if you see an image previously noted on the "end" page, set $almostdone
	#
	my $newstuffseen = 0;
	$done = 1 if $almostdone < 1; # two-step done detection lets us reprocess "end" page
        my $response = $agent->get($url) or die "Unable to fetch $url";

        $content = $response->decoded_content;

        $firstTranslit = fetchTransliteration($content,$startc,$startv,0,$startTranslit1Color,$startTranslit2Color) if ($url eq $firstURL && $translit);
	$p = HTML::TokeParser->new(\$content);
	my $seenForward = 0;
	while (my $token = $p->get_token()) {
		if ($token->[1] eq "table") {
			if ($token->[0] eq "S") {
				$trCount[++$tableDepth] = 0;
			} else {
				$tableDepth--;
			}
		}

		if ($token->[1] eq "tr" && $token->[0] eq "S") {
			$trCount[$tableDepth]++;
		}

		if ($token->[1] eq "img") {
			my $src = $token->[2]{"src"};
			if ($src =~ /^\/webmedia\/t\d\/(.*)\.gif/) {
				$almostdone = 2 if $almostdone > 2 && $imagesInEnd{$src};
				if ($imagesInEnd{$src}) {
					$almostdone = 2 unless $almostdone < 2;
					# force to next page of scrollScraper if ($endc,$endv) verse may be incomplete
					$newstuffseen = 1 unless verseAppearsInURL($url,$endcFollow,$endvFollow);
				} else {
					$newstuffseen = 1;
				}
				if ($1 =~ /\d$/) {
					push @rightOutputs,$src unless $seenRights{$src};
					$lastRight = $src;
					$seenRights{$src}++;
				} else {
					push @leftOutputs,$src unless $seenLefts{$src};
					$seenLefts{$src}++;
				}
			}
		}

		if ($token->[0] eq "S" && $token->[1] eq "a") {
			my $text = $p->get_trimmed_text("/a");
			my $class = $token->[2]{"class"};
			if (defined($text) && $text eq "Forward") {
				$url = $token->[2]{href} || "-";
				$url = $site . $url if ($url =~ /^\//);
				$seenForward = 1;
			} elsif ($class eq "light" || $class eq "dark") {
				$text =~ s/\D*//;
				$verseInfo{$lastRight}{$text} = "$class," . $trCount[$tableDepth];
				$verseShades{$text} = $class;
				$done = 1 if compareChapterAndVerse($text,"$endc:$endv") > 0;
			}
		}
	}

	# look forward to next portion
	if (!$seenForward && $beginPortion < $endPortion) {
		$portion++;
		# now, fetch first verse of the next portion
		my $pI = $parshaInfo[$portion-1];
		if ($pI->[0] == $book) {
			$url = sprintf($base,$book,$pI->[1],$pI->[2],$portion);
		}
	}

	$done = 1 if ($almostdone-- < 1 && !$newstuffseen); # Kohelet 1:9   :-)
	$done = 1 if ($verseShades{"$endcFollow:$endvFollow"});
}


#
# Some remarks are in order regarding how "doShading" is implemented.  Each ORT GIF is 90 pixels high, 445 pixels wide,
# and consists of three vertical lines of Torah text.  For the training text, the verses are alternately shaded
# light-blue and dark-blue.  Furthermore, the original ORT pages contain verse numbers which are also shaded
# following the same convention, and have a vertical row position which corresponds to the starting line
# of that verse in the image.
#
# Above, we harvested the shades, verse number and row number into the %verseInfo and %verseShades data structures.
# Now we're ready to prepare 'maps' of the shading info for the first few and last few images, and correlate
# these maps with the above-mentioned data structures to figure out where (horizontally and vertically) the reading
# begins and ends.
#
# Having computed these horizontal and vertical positions, we then select one of 445x3 pre-generated PNG images to
# overlay on the beginning ORT GIF, and similarly for a different set of 445x3 PNGs for the ending ORT GIF.  The
# overlay is implemented in HTML using z-coordinates and cascading styles.
#


# is our start verse not represented in the first image AND (just to be on the safe side) is it
# represented in the second image?  If so, then let's jettison the first image.  Example:
# Exodus 2:12-20
if (defined $rightOutputs[1] && ! defined $verseInfo{$rightOutputs[0]}{"$startc:$startv"} && defined $verseInfo{$rightOutputs[1]}{"$startc:$startv"}) {
	shift @rightOutputs;
	shift @leftOutputs;
}

my $doEndShading = 1;
my @endtags;

# TODO: these cases should be handled in a loop, but then the code would be even more cryptic
# We are handling the cases where we have fetched several more GIFs than we needed
if (! defined $verseInfo{$rightOutputs[-1]}{"$endc:$endv"}) {
	if (defined $rightOutputs[-4] && defined $verseInfo{$rightOutputs[-4]}{"$endc:$endv"}) {
		my @versesStartingInLateImages = keys %{$verseInfo{$rightOutputs[-4]}};
		push @versesStartingInLateImages,keys %{$verseInfo{$rightOutputs[-3]}};
		push @versesStartingInLateImages,keys %{$verseInfo{$rightOutputs[-2]}};
		foreach my $chAndVerse (@versesStartingInLateImages) {
			if (compareChapterAndVerse($chAndVerse,"$endc:$endv") > 0) {
				pop @rightOutputs;
				pop @leftOutputs;
				last;
			}
		}
	}
}

if (! defined $verseInfo{$rightOutputs[-1]}{"$endc:$endv"}) {
	if (defined $rightOutputs[-3] && defined $verseInfo{$rightOutputs[-3]}{"$endc:$endv"}) {
		my @versesStartingInLateImages = keys %{$verseInfo{$rightOutputs[-3]}};
		push @versesStartingInLateImages,keys %{$verseInfo{$rightOutputs[-2]}};
		foreach my $chAndVerse (@versesStartingInLateImages) {
			if (compareChapterAndVerse($chAndVerse,"$endc:$endv") > 0) {
				pop @rightOutputs;
				pop @leftOutputs;
				last;
			}
		}
	}
}

if (defined $rightOutputs[-2] && ! defined $verseInfo{$rightOutputs[-1]}{"$endc:$endv"} && defined $verseInfo{$rightOutputs[-2]}{"$endc:$endv"}) {
	# last verse starts in penultimate image, but that may not be a problem since it that verse may extend into the final image
	my @versesStartingInPenultimateImage = keys %{$verseInfo{$rightOutputs[-2]}};
	my $doTrim = 0;
	foreach my $chAndVerse (@versesStartingInPenultimateImage) {
		if (compareChapterAndVerse($chAndVerse,"$endc:$endv") > 0) {
			$doTrim = 1;
			last;
		}
	}
	if ($doShading && ! $doTrim) {
		# now consider the final image.  Does it begin with a brand-new verse?  I.e., is the lowest-numbered verse index at "line 1"
		# of the image AND does the color at the beginning of the image match the color of the verse label?  If so, then let's:
		#   (a) trim this image from our output AND
		#   (b) eliminate our new final image (previously the penultimate image) as a candidate for shading.
		my @verses = keys %{$verseInfo{$rightOutputs[-1]}};
		my @sortedVerses = sort { compareChapterAndVerse($a,$b) } @verses;
		my $firstVerse = $sortedVerses[0];
		my ($shade,$row) = split /,/,$verseInfo{$rightOutputs[-1]}{$firstVerse};

		@endtags = tagTikkunRegionsByColorFromURL("$outputSite" . $rightOutputs[-1]);
		my($observedShade, $row1, $x1, $row2, $x2) = @{$endtags[0]};
#		if ($shade eq $observedShade && $row <= $row2) {
		if ($shade eq $observedShade && $row <= $row2 && ($row2 >= 2 || $x2 >= 10)) {
			$doTrim = 1;
			$doEndShading = 0;
			@endtags = (); # we'll no longer use this result, so discard it
		}
	}
	if ($doTrim) {
		pop @rightOutputs;
		pop @leftOutputs;
	}
}

#
#
my ($begLabel, $endLabel);
if ($doShading) {
	my $dbg;
	my @begintags = tagTikkunRegionsByColorFromURL("$outputSite" . $rightOutputs[0]);
	# note that we re-use the @endtags result from above, if it's already been computed, since it's an expensive calculation
	@endtags = tagTikkunRegionsByColorFromURL("$outputSite" . $rightOutputs[-1]) unless @endtags;

	# my @sortedVerses = sort compareChapterAndVerse keys %{$verseInfo{$rightOutputs[0]}};
	if ($verseInfo{$rightOutputs[0]}{"$startc:$startv"}) {
		my ($begshade,$begrow) = split /,/,$verseInfo{$rightOutputs[0]}{"$startc:$startv"};
		for my $tag (@begintags) {
			my($observedShade, $row1, $x1, $row2, $x2) = @{$tag};
			if ($observedShade eq $begshade && $row1 eq $begrow) {
				$x1 -= 5;
				$x1 = 0 if $x1 < 0;
				if ($row1 > 1 && $tag eq $begintags[0]) { # the first tag, but doesn't appear in the first row
					$row1 = 1;
					$x1 = 0;
				}
				$begLabel = "$shadingDir/alpha_TOP" . "$row1" . "_" . "$x1" . ".png";
				last;
			}
		}
	}

	if ($verseInfo{$rightOutputs[-1]}{"$endc:$endv"}) {
		my @sortedVerses = sort { compareChapterAndVerse($a,$b) }  keys %{$verseInfo{$rightOutputs[-1]}};

		my ($endshade,$endrow) = split /,/,$verseInfo{$rightOutputs[-1]}{"$endc:$endv"};
		for my $tag (@endtags) {
			my($observedShade, $row1, $x1, $row2, $x2) = @{$tag};
			if ($sortedVerses[0] eq "$endc:$endv") {
				$x2 -= 0;
				$x2 = 0 if $x2 < 0;
				$x2 = $gifWidth if $x2 > ($gifWidth - 12);
				if ($observedShade eq $endshade && $row1 eq $endrow) {
					$endLabel = "$shadingDir/alpha_BOT" . "$row2" . "_" . ($gifWidth-$x2) . ".png";
					last;
				}
			} else {
				my ($theshade,$therow) = split /,/,$verseInfo{$rightOutputs[-1]}{$sortedVerses[0]};
				if ($observedShade eq $theshade && $row1 eq $therow) { # we've accounted for a verse with this shade
					shift @sortedVerses;
				}
			}
		}
	} else { # we are finishing our verse which was started in the previous GIF (or perhaps even earlier)
		my $tag = $endtags[0];
		my $endshade = $verseShades{"$endc:$endv"};
		my($observedShade, $row1, $x1, $row2, $x2) = @{$tag};
		for my $tag (@endtags) {
			my($observedShade, $row1, $x1, $row2, $x2) = @{$tag};
			$x2 -= 0;
			$x2 = 0 if $x2 < 0;
			$x2 = $gifWidth if $x2 > ($gifWidth - 12);
			if ($observedShade eq $endshade) {
				$endLabel = "$shadingDir/alpha_BOT" . "$row2" . "_" . ($gifWidth-$x2) . ".png";
				last;
			}
		}
	}

	$doShading = 0 unless $begLabel && $endLabel; # if we can't the shading job completely, then let's forget the whole thing
	my $dbg;
}
		

my @title = (getBookName($book,0), getPortionName($beginPortion)," $startc:$startv", "-","$endc:$endv");
print $cacheOutRef "<!DOCTYPE HTML PUBLIC \"-//W3C//DTD HTML 4.01 Transitional//EN\">\n";
print $cacheOutRef "<html>\n<head>\n";
print $cacheOutRef "<title>".join(" ",@title)."</title>\n";
print $cacheOutRef "</head>\n<body>\n";

print $cacheOutRef "<center><h1>".shift(@title)."</h1>\n";
print $cacheOutRef "<h2>".join(" ",@title)."</h2></center>\n"; 
print $cacheOutRef "<hr>";
print $cacheOutRef "<table><tr><td>\n" if $sbs;


print $cacheOutRef "<span style=\"position: relative; top: 0px\">\n" if ($doShading);
foreach (@leftOutputs) {
	print $cacheOutRef "<img alt=\"\" src=\"$outputSite$_\"><br>\n";
	$gifCount++;
}

my $verticalOffset = -1 * ($gifCount * 90 + 90);

if ($doShading) {
	# This left-side "shading" is only performed to workaround a common Web browser printing bug (found in nearly all
	# major browsers except Safari, as of 12/2010).  By making the geometry identical on both left & right sides, we
	# can avoid this problem.
	my $blankLabel = "$shadingDir/$blankImage";
	print $cacheOutRef "<span style=\"position: relative; top: -90px; z-index:2\"><img alt=\"\" src=\"" . $blankLabel . "\"></span><br>\n";
	print $cacheOutRef "<span style=\"position: relative; top: " . $verticalOffset . "px; z-index:2\"><img alt=\"\" src=\"" . $blankLabel . "\"></span><br>\n";
	print $cacheOutRef "</span>\n";
}


print $cacheOutRef "</td><td>\n" if $sbs;
print $cacheOutRef "<br>\n" unless $sbs;
print $cacheOutRef "<span style=\"position: relative; top: 0px\">\n" if ($doShading);
foreach (@rightOutputs) {
	if ($coloring) {
		print $cacheOutRef "<img alt=\"\" src=\"./colorImage.cgi?thegif=$_&coloring=$coloring\"><br>\n";
	} else {
		print $cacheOutRef "<img alt=\"\" src=\"$outputSite$_\"><br>\n";
	}
	$gifCount++;
}

if ($doShading) {
	print $cacheOutRef "<span style=\"position: relative; top: -90px; z-index:2\"><img alt=\"\" src=\"" . $endLabel . "\"></span><br>\n";
	print $cacheOutRef "<span style=\"position: relative; top: " . $verticalOffset . "px; z-index:2\"><img alt=\"\" src=\"" . $begLabel . "\"></span><br>\n";
	print $cacheOutRef "</span>\n";
}

print $cacheOutRef "</td></tr></table>" if $sbs;

if ($translit) {
	print $cacheOutRef "<br><br>" unless $doShading;
	print $cacheOutRef "<hr>Transliteration excerpts for identifying reading start and end:<br>\n";
	print $cacheOutRef "$startc:$startv $firstTranslit<br>\n";
	print $cacheOutRef "$endc:$endv $lastTranslit\n";
}

if ($showStartAndEndButtons) {
	print $cacheOutRef "<br><br><hr><a href=\"$firstURL\" TARGET=\"checkORT\"><img src=\"./checkreadingstartButton.GIF\"></a>\n";
	print $cacheOutRef "<a href=\"$lastURL\" TARGET=\"checkORT\"><img src=\"./checkreadingendButton.GIF\"></a>\n";
}

if ($doAudio) {
#	print $cacheOutRef "<br><br><hr><img src=./new.gif> <a href=\"$mainURL/$smilFileName\">Experimental audio</a>, requires <a href=\"http://www.real.com/player\">Real Player</a> <a href=\"./buildmp3.cgi?flags=$flags&book=$book&startc=$startc&endc=$endc&startv=$startv&endv=$endv&audioRepeatCount=$audioRepeatCount&raFiles=\">*</a>\n";
	print $cacheOutRef "<br><br><hr><a href=\"./buildmp3.cgi?flags=$flags&book=$book&startc=$startc&endc=$endc&startv=$startv&endv=$endv&audioRepeatCount=$audioRepeatCount&raFiles=\">Create MP3 audio file</a>\n";

}

print $cacheOutRef "<br><br><hr>All of the <i>tikkun</i> graphics embedded above";
print $cacheOutRef ", as well as the linked audio recordings," if $doAudio;
print $cacheOutRef " are <font color=\"#990033\">Copyright &copy;</font><font color=\"#990033\"><b>2000</b> <a href=\"http://www.ort.org/\"><b>World ORT</b></a>\n";

print $cacheOutRef "</body>\n";
print $cacheOutRef "<!-- scrollscraper outputVersion=$outputVersion gifCount=$gifCount -->\n";
print $cacheOutRef "</html>\n";

unless ($cacheOpenFailed) {
	close CACHEOUT;

	open CACHEIN,"<$cacheFileName" or die "Unable to read cached file $cacheFileName";
	while(<CACHEIN>) {
		print $_;
	}
	close CACHEIN;
}



sub calcPortion {
	my($book,$chapter,$verse) = @_;
	my $fmted = sprintf("%d.%03d",$chapter,$verse);

	return -1 if ($book <= 0 || $book > 5);

	my $last = -1;
	foreach (@parshaInfo) {
		if ($book == $_->[0]) {
			my $fmted2 = sprintf("%d.%03d",$_->[1],$_->[2]);
			if ($fmted2 > $fmted) {
				return $last;
			}
			$last = $_->[3];
		}
	}

	return $last;
}

sub getPortionName {
	my($index) = @_;
	$_ = $parshaInfo[$index-1];
	return $_->[4] if $_->[3] == $index; # sanity check
	return "";
}

sub getBookName {
	my($book,$inHebrew) = @_;

	return $hebrewBookNames[$book-1] if $inHebrew;
	return $englishBookNames[$book-1];
}

sub fetchTransliteration {
	my($content,$chapter,$verse,$isEnd,$color1,$color2) = @_;

	my $p = HTML::TokeParser->new(\$content);
	my $translit = "";
	my $grabnext = 0;
	my $lastChapterAndVerse = "";

	while (my $token = $p->get_token()) {
		if ($grabnext) {
			if ($token->[0] eq "T") {
				$translit .= $token->[1];
			} else {
				last if ($translit);
			}
		}
		if ($token->[0] eq "T" && $token->[1] =~ /\d+:\d+/) {
			$lastChapterAndVerse = $token->[1];
		}
		if ($token->[0] eq "S" && $token->[1] eq "span" && $lastChapterAndVerse eq "$chapter:$verse") {
			my %temp = %{$token->[2]};
			$grabnext = 1 if $temp{"id"} eq "transliteration";
		}

	}

	if ($translit) {
		if ($isEnd) {
			if ($translit =~ /^(.*\s+)(\S+\s+\S+\s+\S+\s+\S+\s*)$/) {
				return "<font color=\"$color1\">$1</font><font color=\"$color2\"><b> $2</b></font>";
			}
		} else {
			if ($translit =~ /(\S+\s+\S+\s+\S+\s+\S+\s*)(.*$)/) {
				return "<font color=\"$color1\"><b>$1</b></font><font color=\"$color2\"> $2</font>";
			}
		}
	}

	return "<font color=\"$color1\"><b>$translit</b></font>" unless $isEnd;
	return "<font color=\"$color2\"><b>$translit</b></font>";
}

sub rangeToFileName {
	my ($cachebase, $book,$startc,$startv,$endc,$endv,$flags) = @_;

	my $dir = "$cachebase/$book.$startc";
	my $file = "$startv.$endc.$endv.$flags";

	system("mkdir -p $dir");
	return "$dir/$file";
}


sub verseAppearsInURL {
	my($content,$chapter,$verse) = @_;

	my $p = HTML::TokeParser->new(\$content);

	while (my $token = $p->get_token()) {
		if ($token->[0] eq "T" && $token->[1] =~ /\d+:\d+/)
{
			return 1 if $token->[1] eq "$chapter:$verse";
		}
	}

	return 0;
}

sub CachedCopyIsValid {
	my($cacheFileName, $outputVersion) = @_;
	my $valid = 0;

	if (-r $cacheFileName) {
		if (open CACHEIN,"<$cacheFileName") {
			while(<CACHEIN>) {
				if (/^<!--.*scrollscraper outputVersion=(\d+).*gifCount=(\d+)/) {
					$valid = 1 if ($1 >= $outputVersion && $2 >= 4);
				}
					
			}
			close CACHEIN;
		}
	}
	
	return $valid;
}


sub compareChapterAndVerse {
	my($chAndVerse1,$chAndVerse2) = @_;
	my($c1,$v1) = split /:/,$chAndVerse1;
	my($c2,$v2) = split /:/,$chAndVerse2;
	return $v1 <=> $v2 if $c1 == $c2;
	return $c1 <=> $c2;
}


# measure color proximity in terms of Euclidean-distance in the three-dimensional RGB space
sub notClose {
    my ( $thresh, $aR1, $aR2 ) = @_;
    my @a1 = @{$aR1};
    my @a2 = @{$aR2};
    my $dist =
      ( $a1[0] - $a2[0] )**2 + ( $a1[1] - $a2[1] )**2 + ( $a1[2] - $a2[2] )**2;
    return $dist >
      $thresh;    # 5000 corresponds to a distance of ~70, since 70*70 = 4900
}

sub tagTikkunRegionsByColorFromURL {
    my ($theurl) = @_;

    my $response = $agent->get($theurl) or die "Unable to download $theurl";

    my $gifdata = $response->decoded_content;

    return tagTikkunRegionsByColor($gifdata);
}

sub tagTikkunRegionsByColor {
    my ($gifdata) = @_;

    # bible.ort.org images (used in ScrollScraper) have RGB colors:
    #    light blue = 132/132/255
    #    dark blue  = 100/46/201

    my @retval;
    my %colorHash;

    my @colors = ( "132/132/255", "100/46/201" );

    my $width = $gifWidth;
    my $image = GD::Image->newFromGifData($gifdata);

    my $lastColor = 'NONE';
    my ( $startrow,  $startx )  = ( 0, 0 );
    my ( $recentrow, $recentx ) = ( 0, 0 );
    my $lastIteration;

    my $samplingRow = 9;

    my @rgb;    # define it out here for debugging ease
    my %none;

    for ( my $row = 0, my $y = $samplingRow ; $row <= 2 ; $row++, $y += 30 ) {

        for ( my $x = 0 ; $x < $width ; $x++ ) {
            $lastIteration = 1 if $row == 2 && $x == ( $width - 1 );

            my $index =
              $image->getPixel( $width - $x, $y );    # TODO: off-by-one errors?
            unless ( defined( $colorHash{$index} ) ) {
                $colorHash{$index} = determineColor( $image, $index, \@colors );
                my $dbg;
            }
            my $theColor = $colorHash{$index};

            if ( $theColor eq 'NONE' ) {

                #search vertically
                for ( my $y2 = $row*30 ; $y2 < $row*30+30 ; $y2++ ) {
                    my $index = $image->getPixel( $width - $x, $y2 )
                      ;                               # TODO: off-by-one errors?
                    unless ( defined( $colorHash{$index} ) ) {
                        $colorHash{$index} = determineColor( $image, $index, \@colors );
                    }
                    if ( $colorHash{$index} ne 'NONE' ) {
                        $theColor = $colorHash{$index};
                        last;
                    }
                }
		$none{$row}{$x}++ unless $theColor ne 'NONE';
            }

            if ( $lastColor eq 'NONE' && !$lastIteration ) {
                $lastColor = $theColor;
            }
            elsif (
                $lastIteration
                || (   $lastColor ne 'NONE'
                    && $lastColor ne $theColor
                    && $theColor  ne 'NONE' )
              )
            {
                my %votes;
                for ( my $y2 = $row*30 ; $y2 < $row*30+30 ; $y2++ ) {
                    my $index = $image->getPixel( $width - $x, $y2 )
                      ;    # TODO: off-by-one errors?
                    unless ( defined( $colorHash{$index} ) ) {
                        $colorHash{$index} = determineColor( $image, $index, \@colors );
                    }
                    $votes{ $colorHash{$index} }++;
                }
		$votes{$theColor} = 0 unless defined $votes{$theColor};
		$votes{$lastColor} = 0 unless defined $votes{$lastColor};
                if ( $votes{$theColor} > 3 && $votes{$theColor} > 1.2 * $votes{$lastColor} ) {
		    unless (@retval) {
			my $done = 0;
			for (my $row = 2; $row >= 0 && ! $done; $row--) {
		            for (my $x = $width - 1; $x >= 0; $x--) {
			        if (defined $none{$row} && defined($none{$row}{$x})) {
				    $startrow = $row;
				    $startx = $x;
			        } else {
				    $done = 1;
				    last;
			        }
			    }
			}
		    }
		    if ($theColor eq 'NONE' && $lastIteration) { # trim last item backwards as appropriate
			my $done = 0;
			for (my $row = 2; $row >= 0 && ! $done; $row--) {
		            for (my $x = $width - 1; $x >= 0; $x--) {
			        if (defined $none{$row} && defined($none{$row}{$x})) {
				    $recentrow = $row;
				    $recentx = $x;
			        } else {
				    $done = 1;
				    last;
			        }
			    }
			}
		    }
		    if (@retval && $startrow == $recentrow && ($recentx - $startx) < 5) { # region is too small
                        my($lastColor2, $startrow2, $startx2, $recentrow2, $recentx2) = @{pop @retval};
			$startrow = $startrow2-1; # must subtract 1, since 1 was added when pushing it into @retval
			$startx = $startx2;
			$lastColor = $lastColor2;
		    } else {
                        my @res =
                          ( $lastColor, $startrow+1, $startx, $recentrow+1, $recentx );
                        push @retval, [@res];
                        $lastColor = $theColor;
                        $startrow  = $row;
                        $startx    = $x;
	    	    }

                }
            }
            $recentrow = $row;
            $recentx   = $x;
        }
    }

    return @retval;

}

sub determineColor {
    my ( $image, $index, $aRefColors ) = @_;
    my @colors = @{$aRefColors};
    my $retval;

    my @rgb   = $image->rgb($index);
    my $shade = 'light';
    foreach my $color (@colors) {    # for each of our two colors
        my @arr = split /\//, $color;
        unless ( notClose( 5000, \@arr, \@rgb ) ) {
            $retval = $shade;
            last;
        }
        $shade = 'dark';             # for 2nd time through this two-color loop
    }
    $retval = 'NONE' unless defined($retval);
    return $retval;
}





