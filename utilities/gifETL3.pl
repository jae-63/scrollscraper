use strict;

use List::Util qw(min max);
use GD;
use LWP::Simple;

GIF_INFO_CSV="final_outputs/gif_info.csv";

my $gifWidth     = 445;
my $gifRowHeight = 30;
my $gifNumRows   = 3;

my $extendToEdge             = 30;

# some parameters which might need tweaking, for identifying dark-blue vs light-blue vs blank
# text sections
my $windowWidthForSmoothing  = 20;
my $windowWidthForSmoothing  = 1;
my $colorThreshold           = 0.05;
my $minFeaturePixelWidth     = 5;
my $minNoneFeaturePixelWidth = 45;

my $outputSite = "https://scrollscraper.adatshalom.net/webmedia/";
$outputSite = "file://var/opt/scrollscraper/webmedia/" if $ENV{"IS_DOCKER"};

# Derived from bible.ort.org.   Note that both the King James bible and Machon Mamre differ from this!
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

# example: ./4.10/1.13.1.11.html
#         my $dir = "$cachebase/$book.$startc";
#         my $file = "$startv.$endc.$endv.$flags";

# ls webmedia/t?/????????.gif
# Sample: webmedia/t5/3412F100.gif

my @chapterAndVerse2Info;

my $agent = LWP::UserAgent->new;

$agent->ssl_opts(
    verify_hostname => 0,
    SSL_verify_mode => 0x00
);

sub process {
    my (
        $path,
        $C_or_D_or_F,
        $verseStartInfo,
        $book,
        $chapter,
        $verse,
        $isFirstImageForThisVerse,
        $lineNumberOnWhichThisVerseBegins,
        $indexOfVerseStartPositionOnThatLine
    ) = @_;

    my $finalGIF;

    $chapterAndVerse2Info[$book][$chapter][$verse] = {}
      if not defined( $chapterAndVerse2Info[$book][$chapter][$verse] );

    $finalGIF =
      $chapterAndVerse2Info[$book][$chapter][$verse]{'finalGIF'} || '';
    $finalGIF = max( $finalGIF, $path );
    $chapterAndVerse2Info[$book][$chapter][$verse]{'finalGIF'} = $finalGIF;

    # ignoring $isFirstImageForThisVerse which seems incorrect
    my $previousFirstGIF =
      $chapterAndVerse2Info[$book][$chapter][$verse]{'firstGIF'} || '';

    if ( $path le $previousFirstGIF || !$previousFirstGIF ) {
        $chapterAndVerse2Info[$book][$chapter][$verse]{'firstGIF'} = $path;
        $chapterAndVerse2Info[$book][$chapter][$verse]
          {'lineNumberOnWhichThisVerseBegins'} =
          $lineNumberOnWhichThisVerseBegins;
        $chapterAndVerse2Info[$book][$chapter][$verse]
          {'indexOfVerseStartPositionOnThatLine'} =
          $indexOfVerseStartPositionOnThatLine;
    }

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

sub compareChapterAndVerse {
    my ( $chAndVerse1, $chAndVerse2 ) = @_;
    my ( $c1, $v1 )                   = split /:/, $chAndVerse1;
    my ( $c2, $v2 )                   = split /:/, $chAndVerse2;
    return $v1 <=> $v2 if $c1 == $c2;
    return $c1 <=> $c2;
}

sub processGIF {
    my ($filename) = @_;

    processTikkunRowsByColorFromURL( "$outputSite" . $filename );
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

sub processTikkunRowsByColorFromURL {
    my ($theurl) = @_;

    my $response = $agent->get($theurl) or die "Unable to download $theurl";

    my $gifdata = $response->decoded_content;

    my @retval;

    for ( my $row = 0 ; $row < 3 ; $row++ ) {
        my @val = tagTikkunRowByColor( $gifdata, $row );
        $theurl =~ s/^.*webmedia\///;
        print "$theurl,$row," . join( ',', flat(@val) ) . "\n";
        push @retval, [@val];
    }
}

# A recursive list flattener from:
#   https://stackoverflow.com/questions/5166662/perl-what-is-the-easiest-way-to-flatten-a-multidimensional-array
sub flat {    # no prototype for this one to avoid warnings
    return map { ref eq 'ARRAY' ? flat(@$_) : $_ } @_;
}

sub tagTikkunRowByColor {
    my ( $gifdata, $row ) = @_;

    # bible.ort.org images (used in ScrollScraper) have RGB colors:
    #    light blue = 132/132/255
    #    dark blue  = 100/46/201

    my @retval;
    my %colorHash;
    my %minWidth;

    my @colors = ( "132/132/255", "100/46/201" );

    my $width = $gifWidth;
    my $image = GD::Image->newFromGifData($gifdata);

    my $lastColor = 'NONE';

    my @rgb;    # define it out here for debugging ease
    my %none;
    my $startx = 0;
    my $recentx;

    my @unweightedVote;

    for ( my $x = 0 ; $x < $width ; $x++ ) {
        my $theColor = 'NONE';
        my %votes;

        #search vertically
        for (
            my $y2 = $row * $gifRowHeight ;
            $y2 < ( $row + 1 ) * $gifRowHeight ;
            $y2++
          )
        {
            my $index = $image->getPixel( $width - $x, $y2 );
            unless ( defined( $colorHash{$index} ) ) {
                $colorHash{$index} = determineColor( $image, $index, \@colors );
            }
            $votes{ $colorHash{$index} }++;

            $votes{$theColor}  = 0 unless defined $votes{$theColor};
            $votes{$lastColor} = 0 unless defined $votes{$lastColor};
        }
        $unweightedVote[$x] =
          ( $votes{'dark'} - $votes{'light'} ) / $gifRowHeight;
    }

    my @weightedVotes;
    my $lastColor             = 'NONE';
    my $startx                = 0;
    my $sumOfAbsWeightedVotes = 0;   # observational only to help us tune params

    for ( my $x = 0 ; $x < $width ; $x++ ) {

    # smooth each horizontal value in a window, weighted by an inverted parabola
        my $sumOfWeights       = 0;
        my $weightedSumOfVotes = 0;
        for (
            my $w = $x - $windowWidthForSmoothing ;
            $w <= $x + $windowWidthForSmoothing ;
            $w++
          )
        {
            if ( $w >= 0 && $w < $width ) {
                my $delta = $x - $w;
                my $weight =
                  $windowWidthForSmoothing * $windowWidthForSmoothing -
                  ( $delta * $delta );
                $sumOfWeights       += $weight;
                $weightedSumOfVotes += $unweightedVote[$x] * $weight;
            }
        }
        my $scaledVote = $weightedSumOfVotes / $sumOfWeights;
        $sumOfAbsWeightedVotes += abs($scaledVote);

        my $proposedColor;
        if ( abs($scaledVote) > $colorThreshold ) {
            $proposedColor = $scaledVote > 0 ? 'dark' : 'light';
        }
        else {
            $proposedColor = 'NONE';
        }

        if ( $proposedColor ne $lastColor || $x == ( $width - 1 ) )
        {    # might add a new segment
            my $minWidth = $minFeaturePixelWidth;
            $minWidth = $minNoneFeaturePixelWidth if $lastColor eq 'NONE';
            if ( ( $x - $startx ) > $minWidth ) {
                my ( $startxFromPrevSegment, $xFromPrevSegment,
                    $colorFromPrevSegment );
                my $doMerge = 0;

                # look back to see if we should merge
                if ( $#retval >= 0 ) {

                    # for example: 7,18,dark,21,32,dark should get merged
                    (
                        $startxFromPrevSegment, $xFromPrevSegment,
                        $colorFromPrevSegment
                    ) = @{ $retval[-1] };
                    $doMerge = $colorFromPrevSegment eq $lastColor;
                }
                if ($doMerge) {
                    $retval[-1][1] = $x - 1;
                }
                else {
                    push @retval, [ $startx, $x - 1, $lastColor ];
                }
            }
            $startx    = $x;
            $lastColor = $proposedColor;
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

# produce a CSV consisting of:
#    1. Book
#    2. Chapter
#    3. Verse
#    4. name of first GIF which is part of this verse
#    5. name of final GIF which is part of this verse (intermediate GIFs are implicit by order)
#    6. line number (within first GIF) on which this verse begins
#    7. index of this verse's start position (usually 0) on that line
#
#    It would be easy to parse this entire CSV on each ScrollScraper run and then perform quick lookups to
#    obtain all the required data.
#
#    Might also need an ordered list of the GIFs.   It would be easy to compute a hash of GIFname -> index,
#    while reading in that list.   That hash would help with subsequent computations
#
#    Calculating items 6 and 7 above are a bit tricky.    Need to work backwards from the [2] index I think.
#    Special-case the $last_image_was_F as needed.
#
#    In scrollscraper.cgi I think I can populate @leftOutputs and @rightOutputs .     It looks a bit harder
#    to populate %verseInfo and %verseShades although the latter can just be computed on-the-fly from book/chapter/verse
#    using our isDark() function.

# For every verse we want to know (in order) all the GIFs required to present that verse.
# We also want to know in which of those GIFs our verse begins, and on which one of the 3 lines it begins.
# Furthermore, on that line, we want to know N, where our verse is the Nth verse which begins on that line.

my %verseInfo;
my @chapterAndVerse2Info;

my $book    = 1;
my $chapter = 1;
my $verse   = 1;

open INP,"<$GIF_INFO_CSV" or die "Unable to open $GIF_INFO_CSV";

while (<INP>) {
	chomp;
	my @fields = split /,/;
	my($book,$chapter,$verse,$firstGIF,$finalGIF) = ($fields[0],$fields[1],$fields[2],$fields[3],$fields[4]);

	$chapterAndVerse2Info[$book][$chapter][$verse]{'firstGIF'} = $firstGIF;
	$chapterAndVerse2Info[$book][$chapter][$verse]{'finalGIF'} = $finalGIF;
        my $begShade = isDark($book,$chapter,$verse) ? "dark" : "light";
        $verseInfo{"/webmedia/$firstGIF"}{"$chapter:$verse"} = "$begShade," .  $fields[5];
	$chapterAndVerse2Info[$book][$chapter][$verse]{'lineNumberOnWhichThisVerseBegins'} = $fields[5];
	$chapterAndVerse2Info[$book][$chapter][$verse]{'indexOfVerseStartPositionOnThatLine'} = $fields[6];
}
close INP;

my $book = -1;
my $chapter = -1;
my $verse = -1;
my $lastColor = 'dark'; # each of the 5 books starts with the dark shade

my @filenames;
my %fileName2Number;
my $fileNameNumber = 0;
my %mapInfo;

# now read the result of another ETL on STDIN.   We're going to try to augment this with chapter/verse info
#
# Use the %chapterAndVerse2Info data structure, especially 'lineNumberOnWhichThisVerseBegins' to sanity
# check our conclusions
while (<>) {
	chomp;
	my @fields = split /,/;
	my $filename = shift @fields;
	my $row = shift @fields;
        if ($row == 0) {
		push @filenames,$filename;
		$fileName2Number{$filename} = $fileNameNumber++;
                if ($filename =~ /t(\d)\//) {
                        my $newBook = $1;
                        if ($newBook != $book) {
                                  $book = $newBook;
                                  $chapter = 1;
                                  $verse = 1;
                                  $lastColor = 'dark'; # each of the 5 books starts with the dark shade
                        }
                 }
        }
        my @localMapInfo;
        while ($#fields >= 0) {
            	my $startx = shift @fields;
               	my $endx = shift @fields;
               	my $color = shift @fields;
                if ($color ne $lastColor && $color ne 'NONE') {
                    # did we switch colors?  If so then move forward a verse!
		    ($book,$chapter,$verse) = goForward($book,$chapter,$verse,1);
                    $lastColor = $color;
                }
               	push @localMapInfo,[$startx,$endx,$color,$chapter,$verse];
        }
        my @extendedLocalMapInfo;
        my $ind = -1;
        my $revise_next_start=0;
        my $next_start_revised;

        foreach my $map (@localMapInfo) {
            	$ind++;
            	my @extra_element;
            	my ($startx,$endx,$color,$chapter,$verse) = @{$localMapInfo[$ind]};
                if ($revise_next_start) {
                    $startx = $next_start_revised;
                    $revise_next_start = 0;
                }
                $startx = 0 if ($ind == 0 && $startx < $extendToEdge);
                if ($ind >= $#localMapInfo) {
                    if (($gifWidth-$endx) < $extendToEdge) {
                        $endx = $gifWidth-1;
                    } else {
                	 @extra_element = [$endx+1,$gifWidth-1,'NONE',0,0];
                    }
                } else {
                    # insert a 'NONE' block before the next block if there is a gap
            	    my ($next_startx,$next_endx,$next_color,$next_chapter,$next_verse) = @{$localMapInfo[$ind+1]};
                    if (($endx+1) <= ($next_startx-1)) { # ready to add some NONE but let's figure out the right way
                        if ($color eq 'NONE') {
                            $endx = $next_startx-1;
                        } elsif ($next_color eq 'NONE') {
                            $revise_next_start = 1;
                            $next_start_revised = $endx+1;
                        } else {
                	    @extra_element = [$endx+1,$next_startx-1,'NONE',0,0];
                        }
                    }
                }
               	push @extendedLocalMapInfo,[$startx,$endx,$color,$chapter,$verse];
             	push @extendedLocalMapInfo,@extra_element if @extra_element;
        }
        $mapInfo{$filename}{$row} = \@extendedLocalMapInfo;
        print "$filename,$row," . join( ',', flat(@extendedLocalMapInfo) ) . "\n";
}
