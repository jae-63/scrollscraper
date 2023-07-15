use strict;

use List::Util qw(min max);
use GD;
use LWP::Simple;

my $gifWidth     = 445;
my $gifRowHeight = 30;
my $gifNumRows   = 3;

# some parameters which might need tweaking, for identifying dark-blue vs light-blue vs blank
# text sections
my $windowWidthForSmoothing  = 20;
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

    if (length($gifdata) <= 0) {
        return [] if ($ENV{"DUMMY_GIFNAMES_OK"});
        die "Unable to load URL $theurl";
    }

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
my %fileName2Number;
my $fileNameNumber = 0;
my @filenames;

my $book    = 1;
my $chapter = 1;
my $verse   = 1;

my $last_image_was_F = 1;

# Note that we must iterate through all the verses in each chapter
while (<>) {
    chomp;
    my $path = $_;
    $path =~ s/^.*webmedia\///;
    if (/t(\d)\/(\d\d)(\d\d)([FC])(\d\d\d).gif/) {

# $gifVerse is the LAST verse which includes content within this GIF
# Apparently 'F' signifies the end of a paragraph, corresponding roughly to a petukha.   Alternatively,
# think of 'F' as a clean-finish, while 'C' means the verse continues into the next GIF
# 'D' is a GIF which is in the middle of a long verse
        my ( $book, $chapter, $verse, $C_or_D_or_F, $verseStartInfo ) =
          ( int($1), int($2), int($3), $4, $5 );

# $verseStartInfoList is a count of how many verses begin on that line of the (three-line) GIF
        my @verseStartInfoList = split //, $verseStartInfo;
        my $goBackCount =
          $verseStartInfoList[0] +
          $verseStartInfoList[1] +
          $verseStartInfoList[2];
        $goBackCount++ unless $last_image_was_F;

        push @filenames, $path;
        $fileName2Number{$path} = $fileNameNumber++;

        processGIF($path);

        $last_image_was_F = ( $C_or_D_or_F eq 'F' );

        while ( $goBackCount-- > 0 ) {
            my $isFirstImageForThisVerse = ( $goBackCount <= 0 );
            my $lineNumberOnWhichThisVerseBegins;
            my $indexOfVerseStartPositionOnThatLine;
            foreach my $row ( 2, 1, 0 ) {
                if ( $verseStartInfoList[$row] > 0 ) {
                    $lineNumberOnWhichThisVerseBegins = $row;
                    $indexOfVerseStartPositionOnThatLine =
                      --( $verseStartInfoList[$row] );
                    last;
                }
            }
            process(
                $path,
                $C_or_D_or_F,
                $verseStartInfo,
                $book,
                $chapter,
                $verse,
                $isFirstImageForThisVerse,
                $lineNumberOnWhichThisVerseBegins,
                $indexOfVerseStartPositionOnThatLine
            );
            my @results = goBack( $book, $chapter, $verse, 1 );
            ( $book, $chapter, $verse ) = @results;
        }

    }
}

# First of two passes through this data because we need to reference %verseInfo in the second pass
foreach my $book ( 1, 2, 3, 4, 5 ) {
    my $chaptersInBook = @{ $versesPerChapter[ $book - 1 ] };
    my $verseInBook    = -1;                                  # zero-based count
        #	print "$book,$chaptersInBook\n";
    for ( my $chapter = 1 ; $chapter <= $chaptersInBook ; $chapter++ ) {
        my $versesInThisChapter =
          $versesPerChapter[ $book - 1 ][ $chapter - 1 ];
        for ( my $verse = 1 ; $verse <= $versesInThisChapter ; $verse++ ) {
            $verseInBook++;
            my %val = %{ $chapterAndVerse2Info[$book][$chapter][$verse] };
            my $firstGIF =
              $chapterAndVerse2Info[$book][$chapter][$verse]{'firstGIF'};
            my $finalGIF =
              $chapterAndVerse2Info[$book][$chapter][$verse]{'finalGIF'};

            my $firstGIFindex = $fileName2Number{$firstGIF};
            my $finalGIFindex = $fileName2Number{$finalGIF};

            my $lineNumberOnWhichThisVerseBegins =
              $chapterAndVerse2Info[$book][$chapter][$verse]
              {'lineNumberOnWhichThisVerseBegins'};

            my $begShade = isDark( $book, $chapter, $verse ) ? "dark" : "light";

    # our ETL'd rows are zero-based but all the ScrollScraper logic is one-based
            my $rowPlus1 = $lineNumberOnWhichThisVerseBegins + 1;
            $verseInfo{"$firstGIF"}{"$chapter:$verse"} =
              "$begShade," . $rowPlus1;

        }
    }
}

