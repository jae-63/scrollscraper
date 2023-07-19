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
use GD::Text;
use verse2hebrew;
use Data::Dumper;

my $fontFile = "fonts/SILEOTSR.ttf";
my $GIF_INFO_CSV = "final_outputs/gif_info.csv";
my $MAP_CSV = "final_outputs/map.csv";

# sample: https://bible.ort.org/books/torahd5.asp?action=displaypage&book=2&chapter=27&verse=1&portion=19

#
# $outputVersion should be incremented each time the format is changed in
# a manner which affects previously cached output files
#
my $outputVersion = 9;
#
# Provide a debug mode where outputted cached files (executed in that DEBUG mode) don't
# impact the Production views, on the live ScrollScraper server
#
# Sample usage:
#    DEBUG=1 perl ./scrollscraper2.cgi "book=5&audioRepeatCount=1&coloring=0&doShading=on&startc=28&startv=52&endc=28&endv=52"
# where scrollscraper2.cgi is an edited development copy of scrollscraper.cgi
#
$outputVersion-- if defined $ENV{"DEBUG"};

my $site       = "https://bible.ort.org";
my $outputSite = $site;
my $outputSite = "https://scrollscraper.adatshalom.net";
my $base =
"$site/books/torahd5.asp?action=displaypage&book=%d&chapter=%d&verse=%d&portion=%d";
my $gifWidth      = 445;
my $maximumVerseLengthInGIFs = 3;
my $shadingDir    = "ScrollScraperalphaPNGs";
my $forbiddenFile = "forbidden-referers.txt";
my $smilFormat =
"<audio src=\"https://bible.ort.org/webmedia/t%d/%02d%02d.ra\" title=\"%s %d:%d\" %s/>";
my $mainURL      = "http://scrollscraper.adatshalom.net";
my $fliteOptions = "--setf duration_stretch=1.2";   # slow down the audio by 20%
my $fliteSpeechSynthesis = "/home/jepstein/flite/flite-1.3-release/bin/flite";
my $festivalSpeechSynthesis = "/home/jepstein/festival/festival/bin/text2wave";
my $festivalOptions         = "-scale 3 -o";
my $lame =
  "/home/jepstein/lame-3.97/frontend/lame"; # use "lame" for WAV->MP3 conversion

my $cachebase = "./cache/";
my $smilbase  = "./smil/";

my $usage =
  "Usage: " . $0 . " book startchapter startverse endchapter endverse";
my $gifCount = 0;
my $book;
my $startc;
my $startv;
my $endc;
my $endv;
my $sbs                    = 1;
my $translit               = 0;
my $showStartAndEndButtons = 0;
my $useCache               = 1;    # not part of "$flags" below
my $doAudio                = 1;
my $audioRepeatCount       = 1;
my $coloring;
my $generateCache = 1;
my $doShading     = 0;
my $trueTypeFonts = 0;
my %hebrewText;
my %fontSizeOverride;
my $blankImage = "alpha_TOP1_0.png"
  ;    # used for padding on LHS of table, when $doShading is used

my $agent = LWP::UserAgent->new;

$agent->ssl_opts(
    verify_hostname => 0,
    SSL_verify_mode => 0x00
);

my $q = new CGI;

if ( $q->param('book') ) {
    print "Content-type: text/html\n\n";

    foreach my $key ( $q->param ) {
        next if $key eq 'coloring';
        if ( $q->param($key) !~ /^\d+$/ && $q->param($key) !~ /^(on|off)$/ ) {
            my $str = "Invalid parameter: $key=" . $q->param($key);
            print "$str\n";
            die "$str";
        }
    }

    $book             = $q->param('book');
    $startc           = $q->param('startc');
    $startv           = $q->param('startv');
    $endc             = $q->param('endc');
    $endv             = $q->param('endv');
    $sbs              = 1 if $q->param('sbs');
    $sbs              = 0 if $q->param('col1');
    $translit         = 0 if $q->param('notranslit');
    $useCache         = 0 if $q->param('dontUseCache');
    $doAudio          = 0 if $q->param('noAudio');
    $audioRepeatCount = $q->param('audioRepeatCount')
      if $q->param('audioRepeatCount');
    $coloring = ${ \$q->param('coloring') }
      if length( ${ \$q->param('coloring') } ) > 1;
    $doShading     = $q->param('doShading')     if $q->param('doShading');
    $trueTypeFonts = $q->param('trueTypeFonts') if $q->param('trueTypeFonts');

    if ( -f $forbiddenFile && defined $ENV{"HTTP_REFERER"} ) {
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
}
else {
    $book      = shift or die $usage;
    $startc    = shift or die $usage;
    $startv    = shift or die $usage;
    $endc      = shift or die $usage;
    $endv      = shift or die $usage;
    $sbs       = shift;    # optional
    $useCache  = 0;        # JAE TEMP 07/30/09, for development only
    $doShading = 1;        # more debugging code
}

my $flags = $sbs | ( $translit << 1 ) | ( $showStartAndEndButtons << 2 ) |
  ( $doAudio << 3 ) | ( $doShading << 4 ) | ( $trueTypeFonts << 5 );

#$coloring = "25,25,112,25,25,112" if ($ENV{"HTTP_USER_AGENT"} =~ /NetFront.*Kindle/ && ! $coloring);
$coloring = "25,25,112,0,139,139"
  if ( $ENV{"HTTP_USER_AGENT"} =~ /NetFront.*Kindle/ && !$coloring )
  ;    # modest shading for traditional greyscale Kindles
$useCache      = 0 if $coloring;
$generateCache = 0 if $coloring;

my $audioList = "";

my @englishBookNames =
  ( "Genesis", "Exodus", "Leviticus", "Numbers", "Deuteronomy" );
#
# All Hebrew transliterations used here correspond to conventions used on ORT web site
#
my @hebrewBookNames =
  ( "Bereshit", "Shemot", "VaYikra", "BeMidbar", "Devarim" );

# book, start-chapter, start-verse, portion, title
my @parshaInfo = (
    [ 1, 1,  1,  1,  "Bereshit" ],
    [ 1, 6,  9,  2,  "Noach" ],
    [ 1, 12, 1,  3,  "Lech Lecha" ],
    [ 1, 18, 1,  4,  "VaYera" ],
    [ 1, 23, 1,  5,  "Chayey Sarah" ],
    [ 1, 25, 19, 6,  "Toledot" ],
    [ 1, 28, 10, 7,  "VaYetse" ],
    [ 1, 32, 4,  8,  "VaYishlach" ],
    [ 1, 37, 1,  9,  "VaYeshev" ],
    [ 1, 41, 1,  10, "MiKets" ],
    [ 1, 44, 18, 11, "VaYigash" ],
    [ 1, 47, 28, 12, "VaYechi" ],
    [ 2, 1,  1,  13, "Shemot" ],
    [ 2, 6,  2,  14, "VaEra" ],
    [ 2, 10, 1,  15, "Bo" ],
    [ 2, 13, 17, 16, "BeShalach" ],
    [ 2, 18, 1,  17, "Yitro" ],
    [ 2, 21, 1,  18, "Mishpatim" ],
    [ 2, 25, 1,  19, "Terumah" ],
    [ 2, 27, 20, 20, "Tetsaveh" ],
    [ 2, 30, 11, 21, "Ki Tisa" ],
    [ 2, 35, 1,  22, "VaYakhel" ],
    [ 2, 38, 21, 23, "Pekudey" ],
    [ 3, 1,  1,  24, "VaYikra" ],
    [ 3, 6,  1,  25, "Tsav" ],
    [ 3, 9,  1,  26, "Shemini" ],
    [ 3, 12, 1,  27, "Tazria" ],
    [ 3, 14, 1,  28, "Metsora" ],
    [ 3, 16, 1,  29, "Acharey Mot" ],
    [ 3, 19, 1,  30, "Kedoshim" ],
    [ 3, 21, 1,  31, "Emor" ],
    [ 3, 25, 1,  32, "BeHar" ],
    [ 3, 26, 3,  33, "BeChukotay" ],
    [ 4, 1,  1,  34, "BeMidbar" ],
    [ 4, 4,  21, 35, "Naso" ],
    [ 4, 8,  1,  36, "BeHa'alotecha" ],
    [ 4, 13, 1,  37, "Shlach" ],
    [ 4, 16, 1,  38, "Korach" ],
    [ 4, 19, 1,  39, "Chukat" ],
    [ 4, 22, 2,  40, "Balak" ],
    [ 4, 25, 10, 41, "Pinchas" ],
    [ 4, 30, 2,  42, "Matot" ],
    [ 4, 33, 1,  43, "Mas'ey" ],
    [ 5, 1,  1,  44, "Devarim" ],
    [ 5, 3,  23, 45, "VaEtchanan" ],
    [ 5, 7,  12, 46, "Ekev" ],
    [ 5, 11, 26, 47, "Re'eh" ],
    [ 5, 16, 18, 48, "Shoftim" ],
    [ 5, 21, 10, 49, "Ki Tetse" ],
    [ 5, 26, 1,  50, "Ki Tavo" ],
    [ 5, 29, 9,  51, "Nitsavim" ],
    [ 5, 31, 1,  52, "VaYelech" ],
    [ 5, 32, 1,  53, "Ha'azinu" ],
    [ 5, 33, 1,  54, "Vezot HaBerachah" ],
);

# Derived from bible.ort.org.   Note that both the King James bible and Machon Mamre differ from this!
my @fontSizeOverrides = (
    [ 2, 15, 1, 22, 0.65], # Song of the Sea, Exodus 15:1-22
    [ 5, 32, 1, 47, 0.85], # Haazinu, Deuteronomy 32:1-47
);

my @versesPerChapter = (
    [
        31, 25, 24, 26, 32, 22, 24, 22, 29, 32, 32, 20, 18, 24,
        21, 16, 27, 33, 38, 18, 34, 24, 20, 67, 34, 35, 46, 22,
        35, 43, 54, 33, 20, 31, 29, 43, 36, 30, 23, 23, 57, 38,
        34, 34, 28, 34, 31, 22, 33, 26
    ],
    [
        22, 25, 22, 31, 23, 30, 29, 28, 35, 29, 10, 51, 22, 31,
        27, 36, 16, 27, 25, 23, 37, 30, 33, 18, 40, 37, 21, 43,
        46, 38, 18, 35, 23, 35, 35, 38, 29, 31, 43
    ],
    [
        17, 16, 17, 35, 26, 23, 38, 36, 24, 20, 47, 8,  59, 57,
        33, 34, 16, 30, 37, 27, 24, 33, 44, 23, 55, 46, 34
    ],
    [
        54, 34, 51, 49, 31, 27, 89, 26, 23, 36, 35, 16,
        33, 45, 41, 35, 28, 32, 22, 29, 35, 41, 30, 25,
        18, 65, 23, 31, 39, 17, 54, 42, 56, 29, 34, 13
    ],
    [
        46, 37, 29, 49, 30, 25, 26, 20, 29, 22, 32, 31,
        19, 29, 23, 22, 20, 22, 21, 20, 23, 29, 26, 22,
        19, 19, 26, 69, 28, 20, 30, 52, 29, 12
    ],
);

my @chapterAndVerse2Info;
my @filenames;
my %verseInfo;
my %mapInfo;

my @leftOutputs;
my @rightOutputs;

my $defaultFontSize = 17;

# populate font size override hash
foreach my $override (@fontSizeOverrides) {
    my @override = @{$override};
    my($book,$chapter,$startv,$endv,$ratio) = @override;
    for (my $v = $startv; $v <= $endv; $v++) {
        my $newFontSize = int($defaultFontSize * $ratio + 0.5);
        $fontSizeOverride{"$book:$chapter:$v"} = $newFontSize;
    }
}

my $fileNameNumber   = 0;
my %fileName2Number;

my $GIF_INFO_CSV = "final_outputs/gif_info.csv";
my $MAP_CSV = "final_outputs/map.csv";

open GIF_INFO_CSV,"<$GIF_INFO_CSV" or die "Unable to open $GIF_INFO_CSV";
open MAP_CSV,"<$MAP_CSV" or die "Unable to open $MAP_CSV";

while (<GIF_INFO_CSV>) {
    chomp;
    next if /BOOK/;
    next if /FILE/;

    my @fields = split /,/;
    my ( $book, $chapter, $verse, $firstGIF, $finalGIF ) =
      ( $fields[0], $fields[1], $fields[2], $fields[3], $fields[4] );

    $chapterAndVerse2Info[$book][$chapter][$verse]{'firstGIF'} = $firstGIF;
    $chapterAndVerse2Info[$book][$chapter][$verse]{'finalGIF'} = $finalGIF;
    my $begShade = isDark( $book, $chapter, $verse ) ? "dark" : "light";
    $verseInfo{"/webmedia/$firstGIF"}{"$chapter:$verse"} =
      "$begShade," . $fields[5];
    $chapterAndVerse2Info[$book][$chapter][$verse]
      {'lineNumberOnWhichThisVerseBegins'} = $fields[5];
    $chapterAndVerse2Info[$book][$chapter][$verse]
      {'indexOfVerseStartPositionOnThatLine'} = $fields[6];
}

close GIF_INFO_CSV;

while (<MAP_CSV>) {
    chomp;
    next if /FILENAME/;
    next if /BOOK/;
    my @fields   = split /,/;
    my $filename = shift @fields;
    my $row      = shift @fields;
    if ( $row == 0 ) {
        push @filenames, $filename;
        $fileName2Number{$filename} = $fileNameNumber++;
    }
    my @localMapInfo;
    while ( $#fields >= 0 ) {
        my $startx  = shift @fields;
        my $endx    = shift @fields;
        my $color   = shift @fields;
        my $chapter = shift @fields;
        my $verse   = shift @fields;
        push @localMapInfo, [ $startx, $endx, $color, $chapter, $verse ];
    }
    $mapInfo{$filename}{$row} = \@localMapInfo;
}

close MAP_CSV;

my $firstGIFName = $chapterAndVerse2Info[$book][$startc][$startv]{'firstGIF'};
my $finalGIFName = $chapterAndVerse2Info[$book][$endc][$endv]{'finalGIF'};

my $firstGIFIndex = $fileName2Number{$firstGIFName};
my $finalGIFIndex = $fileName2Number{$finalGIFName};

if ( $firstGIFIndex > $finalGIFIndex ) {
    ( $firstGIFIndex, $finalGIFIndex ) = ( $finalGIFIndex, $firstGIFIndex );
    ( $startc, $startv, $endc, $endv ) = ( $endc, $endv, $startc, $startv );
}

#
# the "left" and "right" nomenclature below refer to layout in a traditional
# tikkun, not how it appears on the ORT web pages
#
# i.e.: left  = like it appears in the Torah scroll
#       right = with vowels, punctuation + trop
#

for ( my $gifIndex = $firstGIFIndex ;
    $gifIndex <= $finalGIFIndex ; $gifIndex++ )
{
    $_ = "/webmedia/$filenames[$gifIndex]";
    push @rightOutputs, $_;
    s/...\.gif/.gif/;
    push @leftOutputs, $_;
}

my $url;
my $p;
my $portion;
my $content;
my $firstURL;
my $lastURL;
my $startTranslit1Color = "#009900";
my $startTranslit2Color = "#66ff99";
my $endTranslit1Color   = "#ffff33";
my $endTranslit2Color   = "#cc0000";
my $cacheOpenFailed     = 0;
my $cacheOutRef;
my $smilFileName;

my $maxFetches = 200;    # safety valve;

my $beginPortion   = calcPortion( $book, $startc, $startv );
my $chaptersInBook = $versesPerChapter[ $book - 1 ] + 1;

if ( $doAudio && $endc >= $startc ) {
    system("mkdir -p $smilbase");
    $smilFileName =
      rangeToFileName( $smilbase, $book, $startc, $startv, $endc, $endv,
        $flags )
      . ".smil";
    open SMIL, ">$smilFileName"
      or die "Unable to open $smilFileName for output";
    print SMIL
      "<smil xmlns=\"http://www.w3.org/2001/SMIL20/Language\">\n  <head>\n";

    if ( -x $festivalSpeechSynthesis ) {

#		my $tts = "This is an excerpt from parshat" . getPortionName($beginPortion) . ", " . getBookName($book) . ", Chapter $startc, ";
        my $tts =
            "This is an excerpt from "
          . getBookName($book)
          . ", Chapter $startc, "
          ; # it would be nice to include the Parsha, but the pronounciation is too poor
        if ( $startc != $endc ) {
            $tts .= "verse $startv through chapter $endc verse $endv.";
        }
        else {
            $tts .= "verses $startv through $endv.";
        }

        $tts .=
"  The following recorded materials are copyright world-ORT, 1997, all rights reserved.";
        my $wavFileName =
          rangeToFileName( $smilbase, $book, $startc, $startv, $endc, $endv,
            $flags )
          . ".wav";
        my $audioFileName =
          rangeToFileName( $smilbase, $book, $startc, $startv, $endc, $endv,
            $flags )
          . ".mp3";

# note: if desired, we could run this TTS processing and audio conversion in the background
#		system ("$fliteSpeechSynthesis $fliteOptions \"$tts\" $wavFileName; $lame -h --silent --scale 2 $wavFileName $audioFileName; rm -f $wavFileName");
        system(
"(/bin/echo \"$tts\" | $festivalSpeechSynthesis $festivalOptions $wavFileName; $lame -h --silent --scale 2 $wavFileName $audioFileName; rm -f $wavFileName) &"
        );

# trick from SMIL documentation; create a 1pixelx1pixel region so we can attach a volume-adjustment ("soundLevel") to it
        print SMIL
          "    <layout>\n      <root-layout height=\"1\" width=\"1\"/>\n";

# crank up the volume for the synthesized speech, since natively it's much quieter than the ORT leyning recordings
        print SMIL
"      <region id=\"highvolume\" soundLevel=\"300%\"/>\n    </layout>\n";

        print SMIL "  </head>\n  <body>\n";
        print SMIL "    <audio src=\"$mainURL/$audioFileName\"/>\n";
    }
    else {
        print SMIL "  </head>\n  <body>\n";
    }
    print SMIL "    <seq title=\""
      . getBookName($book)
      . "$startc:$startv-$endc:$endv\"";
    print SMIL " repeat=\"$audioRepeatCount\"" if ( $audioRepeatCount > 1 );
    print SMIL ">\n";

    my $v     = $startv;
    my $c     = $startc;
    my $count = 0;
    $audioList = "";

    while ( $count++ < $maxFetches ) {
        my $extra = "";
        $extra = "begin=\"1.5s\"" if ( $count <= 1 );
        $audioList .= "," if ( $count > 1 );
        $audioList .= sprintf "%02d%02d", $c, $v;
        printf SMIL "      $smilFormat\n", $book, $c, $v, getBookName($book),
          $c, $v, $extra;
        last if ( $c >= $endc && $v >= $endv );
        $v++;
        if ( $v > $versesPerChapter[ $book - 1 ][ $c - 1 ] ) {
            $v = 1;
            $c++;
            last if $c >= $chaptersInBook;
        }
    }
    print SMIL "    </seq>\n  </body>\n</smil>\n";
    close SMIL;
}

my $cacheFileName =
  rangeToFileName( $cachebase, $book, $startc, $startv, $endc, $endv, $flags )
  . ".html";
if ( CachedCopyIsValid( $cacheFileName, $outputVersion ) && $useCache ) {
    if ( open CACHEIN, "<$cacheFileName" ) {
        while (<CACHEIN>) {
            print $_;
        }
        close CACHEIN;
        exit 0;
    }
}

if ( $generateCache && open CACHEOUT, ">$cacheFileName" ) {
    $cacheOutRef = \*CACHEOUT;
    binmode( CACHEOUT, "encoding(UTF-8)" );
}
else {
    $cacheOutRef     = \*STDOUT;
    $cacheOpenFailed = 1;
    binmode( STDOUT, "encoding(UTF-8)" );
}

$portion = $beginPortion;

my $tableDepth = 0;
my @trCount;
my $lastRight;

my $firstTranslit;
my $lastTranslit;

if ($trueTypeFonts) {
    $doShading = 0;
}

#
# Some remarks are in order regarding how "doShading" is implemented.  Each ORT GIF is 90 pixels high, 445 pixels wide,
# and consists of three vertical lines of Torah text.  For the training text, the verses are alternately shaded
# light-blue and dark-blue.  Furthermore, the original ORT pages contain verse numbers which are also shaded
# following the same convention, and have a vertical row position which corresponds to the starting line
# of that verse in the image.
#
# Now we're ready to prepare 'maps' of the shading info for the first few and last few images, and correlate
# these maps with the above-mentioned data structures to figure out where (horizontally and vertically) the reading
# begins and ends.
#
# Having computed these horizontal and vertical positions, we then select one of 445x3 pre-generated PNG images to
# overlay on the beginning ORT GIF, and similarly for a different set of 445x3 PNGs for the ending ORT GIF.  The
# overlay is implemented in HTML using z-coordinates and cascading styles.
#

my $doEndShading = 1;

#
#
my ( $begLabel, $endLabel );

if ($doShading) {
    my $dbg;
    my ( $row2, $x2 );

    my ( $row1, $x1 ) = startRowAndXPosition( $book, $startc, $startv );

    $row1++;    # off-by-one use of 0-based vs 1-based

    if ( defined($row1) && defined($x1) ) {
        $x1 -= 5;
        $x1       = 0 if $x1 < 0;
        $begLabel = "$shadingDir/alpha_TOP" . "$row1" . "_" . "$x1" . ".png";
    }

    my (
        $discardBook,
        $followingChapterAfterThisReading,
        $followingVerseAfterThisReading
    ) = goForward( $book, $endc, $endv, 1 );
    my $firstGIFForTheVerseAfterThisReading =
      $chapterAndVerse2Info[$book][$followingChapterAfterThisReading]
      [$followingVerseAfterThisReading]{'firstGIF'};
    my $GIFindexForTheVerseAfterThisReading =
      $fileName2Number{$firstGIFForTheVerseAfterThisReading};

    # finalGIFIndex

    if ( $finalGIFIndex == $GIFindexForTheVerseAfterThisReading ) {
        ( $row2, $x2 ) = startRowAndXPosition(
            $book,
            $followingChapterAfterThisReading,
            $followingVerseAfterThisReading
        );
    }
    else {
# the final verse of our reading was the end of the GIF, so the end-shading has a fixed-value
        $row2 = 2;
        $x2   = $gifWidth;
    }

    if ( defined($row2) && defined($x2) ) {
        $x2 -= 0;
        $x2 = 0         if $x2 < 0;
        $x2 = $gifWidth if $x2 > ( $gifWidth - 12 );
        $row2++;    # off-by-one use of 0-based vs 1-based
        $endLabel = "$shadingDir/alpha_BOT" . "$row2" . "_"
          . ( $gifWidth - $x2 ) . ".png";
    }

    $doShading = 0
      unless $begLabel
      && $endLabel
      ; # if we can't the shading job completely, then let's forget the whole thing
    my $dbg;
}

my @title = (
    getBookName( $book, 0 ),
    getPortionName($beginPortion),
    " $startc:$startv",
    "-", "$endc:$endv"
);
print $cacheOutRef
  "<!DOCTYPE HTML PUBLIC \"-//W3C//DTD HTML 4.01 Transitional//EN\">\n";
print $cacheOutRef "<html>\n<head>\n";

print $cacheOutRef "<!DOCTYPE html PUBLIC \"-//W3C//DTD XHTML 1.0 Transitional//EN\" \"http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd\">\n";
print $cacheOutRef "<html xmlns=\"http://www.w3.org/1999/xhtml\">\n";
print $cacheOutRef "<head>\n";
print $cacheOutRef "<meta http-equiv=\"Content-Type\" content=\"text/html; charset=UTF-8\" />\n";
print $cacheOutRef "<title>" . join( " ", @title ) . "</title>\n";

my $trueTypeBufferedOutput = "<span style=\"position: relative; top: 0px; max-width: 445px; display: block\">";

if ($trueTypeFonts) {
    print $cacheOutRef "<style type=\"text/css\">\n";
    print $cacheOutRef "\@font-face {\n";
    print $cacheOutRef "     font-family: \"hebrewFont\"\;";
    print $cacheOutRef "     src: url(\"$fontFile\")\;\n";
    print $cacheOutRef "}\n";

    my @colors = ( "132,132,255", "100,46,201" );
    if ($coloring) {
        my @fields = split /,/, $coloring;
        $colors[0] = join( ',', $fields[0], $fields[1], $fields[2] );
        $colors[1] = join( ',', $fields[3], $fields[4], $fields[5] );
    }
    my $shade = "light";

    print $cacheOutRef ":root {\n";

    foreach my $color (@colors) {    # for each of our two colors
        my @arr = split /,/, $color;
        my $hex = sprintf( "%02x%02x%02x", $arr[0], $arr[1], $arr[2] );
        print $cacheOutRef "  --our${shade}text: #${hex}\;\n";
        print $cacheOutRef "  --ourobscured${shade}text: #${hex}40\;\n";
        $shade = "dark";
    }
    print $cacheOutRef "}\n";
    print $cacheOutRef "span.dummy {\n";
    print $cacheOutRef "background-color:red\;\n";
    print $cacheOutRef "width:100\%\;\n";
    print $cacheOutRef "height:0em\;\n";
    print $cacheOutRef "display:inline-block\;\n";
    print $cacheOutRef "}\n";

    print $cacheOutRef
"div.sep { font-family: hebrewFont; font-size: 18px; float: left; width: 4px; text-align: right; height: 30px }\n";


# Part of the processing involves GIFs before and after the images which will
# actually be displayed, since we need to calculate the entire length of the 
# truncated Hebrew verse which appears at the beginning of the reading, and
# analogously at the end of the reading.

    my @divNames;
    my %verses2rowRegions;
    my %divName2Hebrew;
    my %rightGIFsToBeDisplayed;

    for ( my $gifIndex = $firstGIFIndex-$maximumVerseLengthInGIFs ;
        $gifIndex <= $finalGIFIndex+$maximumVerseLengthInGIFs ; $gifIndex++ ) {
        next if ($gifIndex < 0 || $gifIndex >= $#filenames);
        $_ = $filenames[$gifIndex];
        s/\/webmedia\///;
        my $strippedGIFname = $_;
        $strippedGIFname =~ s/\//-/;
        $strippedGIFname =~ s/\.gif//;
        $rightGIFsToBeDisplayed{$strippedGIFname}++ if ($gifIndex >= $firstGIFIndex && $gifIndex <= $finalGIFIndex);

        for ( my $row = 0 ; $row < 3 ; $row++ ) {
            my @localMapInfo = @{ $mapInfo{$_}{$row} };

            # traversing forward, i.e. right-to-left to process Hebrew sensibly
            my $rightToLeftPosition = -1;
            my $leftToRightPosition = $#localMapInfo + 1;
            foreach my $map (@localMapInfo) {
                my @mapA    = @{$map};
                my $startx  = $mapA[0];
                my $endx    = $mapA[1];
                my $color   = $mapA[2];
                my $chapter = $mapA[3];
                my $verse   = $mapA[4];
                $rightToLeftPosition++;
                $leftToRightPosition--;
                my $lenx = $endx - $startx + 1;
                next if ( $color eq "NONE" );

                my $divNameBase;
                $divNameBase = $strippedGIFname . "-" . $row;

                my $fullDivName = $divNameBase . "-" . $leftToRightPosition;
                my $formattedVerseName =
                  sprintf( "%02d%03d%03d", $book, $chapter, $verse );
                push @{ $verses2rowRegions{$formattedVerseName} },
                  [ $fullDivName, $lenx ];
                my $dbg;
            }
        }
    }

    foreach my $formattedVerseName ( keys %verses2rowRegions ) {
        my @verseRegionLengths;
        foreach
          my $region ( @{ @{ verses2rowRegions { $formattedVerseName } } } )
        {
            push @verseRegionLengths, @{$region}[1];
        }
        my $hebrewText = hebrew($formattedVerseName);
        my @hebrewRegions =
          partitionHebrewVerse( $hebrewText, $fontFile, @verseRegionLengths );
        foreach
          my $region ( @{ @{ verses2rowRegions { $formattedVerseName } } } )
        {
            my $fullDivName = @{$region}[0];
            $divName2Hebrew{$fullDivName} = shift @hebrewRegions;
        }

        my $dbg;
    }

    my $dbg;

    foreach (@rightOutputs) {
        s/\/webmedia\///;
        my $strippedGIFname = $_;
        $strippedGIFname =~ s/\//-/;
        $strippedGIFname =~ s/\.gif//;

        for ( my $row = 0 ; $row < 3 ; $row++ ) {
            my @localMapInfo = @{ $mapInfo{$_}{$row} };

          # traversing in reverse, which essentially means left-to-right despite
          # the use of Hebrew.   Since HTML operates left-to-right
            my $leftToRightPosition = -1;
            foreach my $map ( reverse @localMapInfo ) {
                my @mapA    = @{$map};
                my $startx  = $mapA[0];
                my $endx    = $mapA[1];
                my $color   = $mapA[2];
                my $chapter = $mapA[3];
                my $verse   = $mapA[4];
                $leftToRightPosition++;

                # boolean: is this verse within the requested reading section?
                my $withinReading =
                  compareChapterAndVerse( "$startc:$startv", "$chapter:$verse" )
                  <= 0
                  && compareChapterAndVerse( "$endc:$endv", "$chapter:$verse" )
                  >= 0;

                my $divNameBase;
                $divNameBase = $strippedGIFname . "-" . $row;
                my $fullDivName = $divNameBase . "-" . $leftToRightPosition;
                push @divNames, $fullDivName;
                my $lenx      = $endx - $startx + 1;
                my $fontSize  = $fontSizeOverride{"$book:$chapter:$verse"} || $defaultFontSize;
                my $colorName = "--our"
                  . ( $withinReading ? "" : "obscured" )
                  . "${color}text";
                if ($color eq "NONE") {
                    print $cacheOutRef "div.$fullDivName { width: ${lenx}px; float: left; text-align: right; height: 30px }\n";
                    $trueTypeBufferedOutput .=
"<div class=$fullDivName><span style=\"position: relative; top: 0px\"> </span><span class=dummy> </span></div>\n";
                } else {
                    print $cacheOutRef
"div.$fullDivName { width: ${lenx}px; font-family: hebrewFont; font-size: $fontSize; color: var($colorName); float: left; text-align: justify; height: 30px }\n";
                    my $hebrew = $divName2Hebrew{$fullDivName};
                    next unless $hebrew;
                    $trueTypeBufferedOutput .=
"<div class=$fullDivName><span style=\"position: relative; top: 0px\">$hebrew</span><span class=dummy> </span></div>\n";
                }

            }
        }
    }
    print $cacheOutRef "</style>\n";
}

print $cacheOutRef "</head>\n<body>\n";

print $cacheOutRef "<center><h1>" . shift(@title) . "</h1>\n";
print $cacheOutRef "<h2>" . join( " ", @title ) . "</h2></center>\n";
print $cacheOutRef "<hr>";
print $cacheOutRef "<table><tr><td>\n" if $sbs;

print $cacheOutRef "<span style=\"position: relative; top: 0px\">\n"
  if ( $doShading || $trueTypeFonts );
foreach (@leftOutputs) {
    print $cacheOutRef "<img alt=\"\" src=\"$outputSite$_\"><br>\n";
    $gifCount++;
}

my $verticalOffset = -1 * ( $gifCount * 90 + 90 );

if ( $doShading ) {

# This left-side "shading" is only performed to workaround a common Web browser printing bug (found in nearly all
# major browsers except Safari, as of 12/2010).  By making the geometry identical on both left & right sides, we
# can avoid this problem.
    my $blankLabel = "$shadingDir/$blankImage";
    print $cacheOutRef
"<span style=\"position: relative; top: -90px; z-index:2\"><img alt=\"\" src=\""
      . $blankLabel
      . "\"></span><br>\n";
    print $cacheOutRef "<span style=\"position: relative; top: "
      . $verticalOffset
      . "px; z-index:2\"><img alt=\"\" src=\""
      . $blankLabel
      . "\"></span><br>\n";
    print $cacheOutRef "</span>\n";
}

print $cacheOutRef "</td><td>\n" if $sbs;
print $cacheOutRef "<br>\n" unless $sbs;
print $cacheOutRef "<span style=\"position: relative; top: 0px\">\n"
  if ($doShading);

if ($trueTypeFonts) {
    print $cacheOutRef "$trueTypeBufferedOutput";
}
else {
    foreach (@rightOutputs) {
        if ($coloring) {
            print $cacheOutRef
"<img alt=\"\" src=\"./colorImage.cgi?thegif=$_&coloring=$coloring\"><br>\n";
        }
        else {
            print $cacheOutRef
              "<img alt=\"\" src=\"$outputSite/$_\"><br>\n";
        }
        $gifCount++;
    }
}

if ($doShading) {
    print $cacheOutRef
"<span style=\"position: relative; top: -90px; z-index:2\"><img alt=\"\" src=\""
      . $endLabel
      . "\"></span><br>\n";
    print $cacheOutRef "<span style=\"position: relative; top: "
      . $verticalOffset
      . "px; z-index:2\"><img alt=\"\" src=\""
      . $begLabel
      . "\"></span><br>\n";
    print $cacheOutRef "</span>\n";
}

print $cacheOutRef "</td></tr></table>" if $sbs;

if ($translit) {
    print $cacheOutRef "<br><br>" unless $doShading;
    print $cacheOutRef
"<hr>Transliteration excerpts for identifying reading start and end:<br>\n";
    print $cacheOutRef "$startc:$startv $firstTranslit<br>\n";
    print $cacheOutRef "$endc:$endv $lastTranslit\n";
}

if ($doAudio) {

#	print $cacheOutRef "<br><br><hr><img src=./new.gif> <a href=\"$mainURL/$smilFileName\">Experimental audio</a>, requires <a href=\"http://www.real.com/player\">Real Player</a> <a href=\"./buildmp3.cgi?flags=$flags&book=$book&startc=$startc&endc=$endc&startv=$startv&endv=$endv&audioRepeatCount=$audioRepeatCount&raFiles=\">*</a>\n";
    print $cacheOutRef
"<br><br><hr><a href=\"./buildmp3.cgi?flags=$flags&book=$book&startc=$startc&endc=$endc&startv=$startv&endv=$endv&audioRepeatCount=$audioRepeatCount&raFiles=\">Create MP3 audio file</a>\n";

}

print $cacheOutRef
  "<br><br><hr>All of the <i>tikkun</i> graphics embedded above";
print $cacheOutRef ", as well as the linked audio recordings," if $doAudio;
print $cacheOutRef
" are <font color=\"#990033\">Copyright &copy;</font><font color=\"#990033\"><b>2000</b> <a href=\"http://www.ort.org/\"><b>World ORT</b></a>\n";

print $cacheOutRef "</body>\n";
print $cacheOutRef
  "<!-- scrollscraper outputVersion=$outputVersion gifCount=$gifCount -->\n";
print $cacheOutRef "</html>\n";

unless ($cacheOpenFailed) {
    close CACHEOUT;

    open CACHEIN, "<$cacheFileName"
      or die "Unable to read cached file $cacheFileName";
    while (<CACHEIN>) {
        print $_;
    }
    close CACHEIN;
}

sub calcPortion {
    my ( $book, $chapter, $verse ) = @_;
    my $fmted = sprintf( "%d.%03d", $chapter, $verse );

    return -1 if ( $book <= 0 || $book > 5 );

    my $last = -1;
    foreach (@parshaInfo) {
        if ( $book == $_->[0] ) {
            my $fmted2 = sprintf( "%d.%03d", $_->[1], $_->[2] );
            if ( $fmted2 > $fmted ) {
                return $last;
            }
            $last = $_->[3];
        }
    }

    return $last;
}

sub getPortionName {
    my ($index) = @_;
    $_ = $parshaInfo[ $index - 1 ];
    return $_->[4] if $_->[3] == $index;    # sanity check
    return "";
}

sub getBookName {
    my ( $book, $inHebrew ) = @_;

    return $hebrewBookNames[ $book - 1 ] if $inHebrew;
    return $englishBookNames[ $book - 1 ];
}

sub fetchTransliteration {
    my ( $content, $chapter, $verse, $isEnd, $color1, $color2 ) = @_;

    my $p                   = HTML::TokeParser->new( \$content );
    my $translit            = "";
    my $grabnext            = 0;
    my $lastChapterAndVerse = "";

    while ( my $token = $p->get_token() ) {
        if ($grabnext) {
            if ( $token->[0] eq "T" ) {
                $translit .= $token->[1];
            }
            else {
                last if ($translit);
            }
        }
        if ( $token->[0] eq "T" && $token->[1] =~ /\d+:\d+/ ) {
            $lastChapterAndVerse = $token->[1];
        }
        if (   $token->[0] eq "S"
            && $token->[1] eq "span"
            && $lastChapterAndVerse eq "$chapter:$verse" )
        {
            my %temp = %{ $token->[2] };
            $grabnext = 1 if $temp{"id"} eq "transliteration";
        }

    }

    if ($translit) {
        if ($isEnd) {
            if ( $translit =~ /^(.*\s+)(\S+\s+\S+\s+\S+\s+\S+\s*)$/ ) {
                return
"<font color=\"$color1\">$1</font><font color=\"$color2\"><b> $2</b></font>";
            }
        }
        else {
            if ( $translit =~ /(\S+\s+\S+\s+\S+\s+\S+\s*)(.*$)/ ) {
                return
"<font color=\"$color1\"><b>$1</b></font><font color=\"$color2\"> $2</font>";
            }
        }
    }

    return "<font color=\"$color1\"><b>$translit</b></font>" unless $isEnd;
    return "<font color=\"$color2\"><b>$translit</b></font>";
}

sub rangeToFileName {
    my ( $cachebase, $book, $startc, $startv, $endc, $endv, $flags ) = @_;

    my $dir  = "$cachebase/$book.$startc";
    my $file = "$startv.$endc.$endv.$flags";

    system("mkdir -p $dir");
    return "$dir/$file";
}

sub verseAppearsInURL {
    my ( $content, $chapter, $verse ) = @_;

    my $p = HTML::TokeParser->new( \$content );

    while ( my $token = $p->get_token() ) {
        if ( $token->[0] eq "T" && $token->[1] =~ /\d+:\d+/ ) {
            return 1 if $token->[1] eq "$chapter:$verse";
        }
    }

    return 0;
}

sub CachedCopyIsValid {
    my ( $cacheFileName, $outputVersion ) = @_;
    my $valid = 0;

    if ( -r $cacheFileName ) {
        if ( open CACHEIN, "<$cacheFileName" ) {
            while (<CACHEIN>) {
                if (/^<!--.*scrollscraper outputVersion=(\d+).*gifCount=(\d+)/)
                {
                    $valid = 1 if ( $1 >= $outputVersion && $2 >= 4 );
                }

            }
            close CACHEIN;
        }
    }

    return $valid;
}

sub compareChapterAndVerse {
    my ( $chAndVerse1, $chAndVerse2 ) = @_;
    my ( $c1, $v1 )                   = split /:/, $chAndVerse1;
    my ( $c2, $v2 )                   = split /:/, $chAndVerse2;
    return $v1 <=> $v2 if $c1 == $c2;
    return $c1 <=> $c2;
}

sub goForward {
    my ( $book, $chapter, $verse, $go_forward_count ) = @_;
    while ( $go_forward_count-- > 0 ) {
        my $versesInThisChapter =
          $versesPerChapter[ $book - 1 ][ $chapter - 1 ];
        $verse++;
        if ( $verse > $versesInThisChapter ) {
            $chapter++;
            $verse = 1;
        }
    }

    return $book, $chapter, $verse;
}

sub goBack {
    my ( $book, $chapter, $verse, $go_back_count ) = @_;
    while ( $go_back_count-- > 0 ) {
        if ( $verse-- <= 1 ) {
            $chapter--;
            my $versesInThisChapter =
              $versesPerChapter[ $book - 1 ][ $chapter - 1 ];
            $verse = $versesInThisChapter;
        }
    }

    return $book, $chapter, $verse;
}

# Note that each of the five books begin with a dark-blue verse, and then light-blue verses are alternated thereafter
sub isDark {
    my ( $book, $chapter, $verse ) = @_;

    my $chaptersInBook = @{ $versesPerChapter[ $book - 1 ] };

    my $verseCount = 0;
    for ( my $ch = 1 ; $ch < $chapter ; $ch++ ) {
        my $versesInThisChapter = $versesPerChapter[ $book - 1 ][ $ch - 1 ];
        $verseCount += $versesInThisChapter;
    }

    $verseCount += $verse;

    return $verseCount % 2;
}

sub abs {
    my ($x) = @_;
    return ( $x > 0 ) ? $x : -$x;
}

sub match_all_positions {
    my ( $regex, $string ) = @_;
    my @ret;
    while ( $string =~ /$regex/g ) { push @ret, $-[0] }
    return @ret;
}

# partition a single Hebrew verse over one or more horizontal regions
# have a prescribed width.
#
# returns an array of Hebrew strings, one per input pixel-width
sub partitionHebrewVerse {
    my $verse             = shift;
    my $fontFile          = shift;
    my @prefixPixelWidths = @_;

    # ptSize doesn't matter much because we wind up calculating everything in
    # proportion to the @verseCoordinates dimensions which are passed to the
    # function partitionHebrewVerse().   ptSize is used, but its influence
    # "washes out" over the course of the calculations
    my $ptSize = 24;

    my @retval;

    my $totalPixelWidth = 0;
    foreach my $prefixPixelWidth (@prefixPixelWidths) {
        $totalPixelWidth += $prefixPixelWidth;
    }

    my @fractionOfTotalWidth;
    foreach my $prefixPixelWidth (@prefixPixelWidths) {
        my $fraction = $prefixPixelWidth / $totalPixelWidth;
        push @fractionOfTotalWidth, $fraction;
    }

    my @original_positions =
      match_all_positions( '[\p{Separator}\p{Dash_Punctuation}]+', $verse );

# There must be a better way to use regex's correctly to include the matched separators, but
# using this hack for now
    my @positions;
    foreach my $pos (@original_positions) {
        my $position;
        my $str = substr( $verse, $pos );
        if ( $str =~ /^[\p{Separator}\p{Dash_Punctuation}]+/ ) {
            push @positions, ( $pos + length($&) );
        }
        else {
            push @positions, $pos;
        }
    }

    # append another position for the end of the string
    if ( $verse =~ /$/ ) { push @positions, $-[0] }

    my @fragmentFontWidths;
    foreach my $position (@positions) {
        my $str     = substr( $verse, 0, $position );
        my $gd_text = GD::Text->new(
            text   => $str,
            font   => $fontFile,
            ptsize => $ptSize
        );

        my ( $w, $h ) = $gd_text->get( 'width', 'height' );
        push @fragmentFontWidths, $w;
    }

    my $totalFragmentFontWidth = $fragmentFontWidths[-1];

    my $lastPosition              = 0;
    my $localFractionOfTotalWidth = 0;

# select the prefix word string whose length best matches the target proportion of the
# "fraction of total width" of the entire verse, for the target output line in-question
    foreach my $fractionOfTotalWidth (@fractionOfTotalWidth) {
        $localFractionOfTotalWidth += $fractionOfTotalWidth;
        my $index             = 0;
        my $bestPositionMatch = -1;
        my $minVal            = 9999999;

        foreach my $fragmentFontWidth (@fragmentFontWidths) {
            my $val = abs( ( $fragmentFontWidth / $totalFragmentFontWidth ) -
                  $localFractionOfTotalWidth );
            if ( $val < $minVal ) {
                $minVal            = $val;
                $bestPositionMatch = $index;
            }
            $index++;
        }
        my $str = substr( $verse, $lastPosition,
            $positions[$bestPositionMatch] - $lastPosition );
        $lastPosition = $positions[$bestPositionMatch];
        push @retval, $str;
    }

    return @retval;

}

sub startRowAndXPosition {

    # returns (startRow,startX)

    my ( $book, $chapter, $verse ) = @_;
    my $theGIF   = $chapterAndVerse2Info[$book][$chapter][$verse]{'firstGIF'};
    my $startRow = $chapterAndVerse2Info[$book][$chapter][$verse]
      {'lineNumberOnWhichThisVerseBegins'};
    my $indexOfVerseStartPositionOnThatLine =
      $chapterAndVerse2Info[$book][$chapter][$verse]
      {'indexOfVerseStartPositionOnThatLine'};

    my @localMapInfo = @{ $mapInfo{$theGIF}{$startRow} };
    my $beginshade   = isDark( $book, $chapter, $verse ) ? "dark" : "light";

    my $remainingCount = $indexOfVerseStartPositionOnThatLine
      ;    # usually 0 (for all but a handful of verses)

# Now traverse @localMapInfo and find the first map-element (from right-to-left in Hebrew)
# which matches our $chapter and $verse
    foreach my $map (@localMapInfo) {
        my @mapA = @{$map};

        # [$startx,$endx,$color,$chapter,$verse]
        if ( $mapA[3] eq $chapter && $mapA[4] eq $verse ) {
            return ( $startRow, $mapA[0] );
        }
    }

    # error case should never occur
    return [];
}

