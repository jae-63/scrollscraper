use strict;

use List::Util qw(min max);
use GD;
use LWP::Simple;

my $gifWidth = 445;
my $gifHeight = 90;

my $outputSite = "https://scrollscraper.adatshalom.net/webmedia/";

# Derived from bible.ort.org.   Note that both the King James bible and Machon Mamre differ from this!
my @versesPerChapter = (
[31,25,24,26,32,22,24,22,29,32,32,20,18,24,21,16,27,33,38,18,34,24,20,67,34,35,46,22,35,43,54,33,20,31,29,43,36,30,23,23,57,38,34,34,28,34,31,22,33,26],
[22,25,22,31,23,30,29,28,35,29,10,51,22,31,27,36,16,27,25,23,37,30,33,18,40,37,21,43,46,38,18,35,23,35,35,38,29,31,43],
[17,16,17,35,26,23,38,36,24,20,47,8,59,57,33,34,16,30,37,27,24,33,44,23,55,46,34],
[54,34,51,49,31,27,89,26,23,36,35,16,33,45,41,35,28,32,22,29,35,41,30,25,18,65,23,31,39,17,54,42,56,29,34,13],
[46,37,29,49,30,25,26,20,29,22,32,31,19,29,23,22,20,22,21,20,23,29,26,22,19,19,26,69,28,20,30,52,29,12],
);

# example: ./4.10/1.13.1.11.html
#         my $dir = "$cachebase/$book.$startc";
#         my $file = "$startv.$endc.$endv.$flags";


# ls webmedia/t?/????????.gif
# Sample: webmedia/t5/3412F100.gif

my @chapterAndVerse2Info;

my $agent = LWP::UserAgent->new;

$agent->ssl_opts(verify_hostname => 0,
              SSL_verify_mode => 0x00);

sub process {
     my($path,$C_or_D_or_F,$verseStartInfo,$book,$chapter,$verse,$isFirstImageForThisVerse,$lineNumberOnWhichThisVerseBegins,$indexOfVerseStartPositionOnThatLine) = @_;

     my $finalGIF;


     $chapterAndVerse2Info[$book][$chapter][$verse] = {} if not defined($chapterAndVerse2Info[$book][$chapter][$verse]);

     $finalGIF = $chapterAndVerse2Info[$book][$chapter][$verse]{'finalGIF'} || '';
     $finalGIF = max($finalGIF,$path);
     $chapterAndVerse2Info[$book][$chapter][$verse]{'finalGIF'} = $finalGIF;

     # ignoring $isFirstImageForThisVerse which seems incorrect
     my $previousFirstGIF = $chapterAndVerse2Info[$book][$chapter][$verse]{'firstGIF'} || '';

     if ($path le $previousFirstGIF || !$previousFirstGIF) {
	      $chapterAndVerse2Info[$book][$chapter][$verse]{'firstGIF'} = $path;
	      $chapterAndVerse2Info[$book][$chapter][$verse]{'lineNumberOnWhichThisVerseBegins'} = $lineNumberOnWhichThisVerseBegins;
	      $chapterAndVerse2Info[$book][$chapter][$verse]{'indexOfVerseStartPositionOnThatLine'} = $indexOfVerseStartPositionOnThatLine;
     }


}

sub goBack {
     my($book,$chapter,$verse,$go_back_count) = @_;
     while ($go_back_count-- > 0) {
	     if ($verse-- <= 1) {
		     $chapter--;
		     my $versesInThisChapter = $versesPerChapter[$book-1][$chapter-1];
		     $verse = $versesInThisChapter;
	     }
     }

     return $book,$chapter,$verse;
}

sub goForward {
     my($book,$chapter,$verse,$go_forward_count) = @_;
     while ($go_forward_count-- > 0) {
	     my $versesInThisChapter = $versesPerChapter[$book-1][$chapter-1];
             $verse++;
	     if ($verse >= $versesInThisChapter) {
		     $chapter++;
		     $verse = 1;
	     }
     }

     return $book,$chapter,$verse;
}

# Note that each of the five books begin with a dark-blue verse, and then light-blue verses are alternated thereafter
sub isDark {
     my($book,$chapter,$verse) = @_;

     my $chaptersInBook = @{$versesPerChapter[$book-1]};

     my $verseCount = 0;
     for (my $ch = 1; $ch < $chapter; $ch++) {
             my $versesInThisChapter = $versesPerChapter[$book-1][$ch-1];
             $verseCount += $versesInThisChapter;
     }

     $verseCount += $verse;

     return $verseCount % 2;
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
    my %notNone;

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
		$notNone{$row}{$x}++ unless $theColor eq 'NONE';
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
			# skip rows which contain no colored text
                        while ($startrow < $row && scalar(keys %{$notNone{$startrow}}) <= 0) {
                                $startrow++;
                        }
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

my $book = 1;
my $chapter = 1;
my $verse = 1;

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
		my($book,$chapter,$verse,$C_or_D_or_F,$verseStartInfo) = (int($1),int($2),int($3),$4,$5);
		# $verseStartInfoList is a count of how many verses begin on that line of the (three-line) GIF
		my @verseStartInfoList = split //,$verseStartInfo;
		my $goBackCount = $verseStartInfoList[0] + $verseStartInfoList[1] + $verseStartInfoList[2];
		$goBackCount++ unless $last_image_was_F;

                $fileName2Number{$path} = $fileNameNumber++;

		$last_image_was_F = ($C_or_D_or_F eq 'F');

		while ($goBackCount-- > 0) {
		    my $isFirstImageForThisVerse = ($goBackCount <= 0);
		    my $lineNumberOnWhichThisVerseBegins;
		    my $indexOfVerseStartPositionOnThatLine;
		    foreach my $row (2,1,0) {
		        if ($verseStartInfoList[$row] > 0) {
			    $lineNumberOnWhichThisVerseBegins = $row;
			    $indexOfVerseStartPositionOnThatLine = --($verseStartInfoList[$row]);
			    last;
		        }
	            }
		    process($path,$C_or_D_or_F,$verseStartInfo,$book,$chapter,$verse,$isFirstImageForThisVerse,$lineNumberOnWhichThisVerseBegins,$indexOfVerseStartPositionOnThatLine);
                    my @results = goBack($book,$chapter,$verse,1);
                    ($book,$chapter,$verse) = @results;
	        }

       }
}


# First of two passes through this data because we need to reference %verseInfo in the second pass
foreach my $book (1,2,3,4,5) {
	my $chaptersInBook = @{$versesPerChapter[$book-1]};
        my $verseInBook = -1; # zero-based count
	#	print "$book,$chaptersInBook\n";
	for (my $chapter=1; $chapter <= $chaptersInBook; $chapter++) {
	     my $versesInThisChapter = $versesPerChapter[$book-1][$chapter-1];
	     for (my $verse=1; $verse <= $versesInThisChapter; $verse++) {
                  $verseInBook++;
	          my %val = %{$chapterAndVerse2Info[$book][$chapter][$verse]};
	          my $firstGIF = $chapterAndVerse2Info[$book][$chapter][$verse]{'firstGIF'};
	          my $finalGIF = $chapterAndVerse2Info[$book][$chapter][$verse]{'finalGIF'};

	          my $firstGIFindex = $fileName2Number{$firstGIF};
	          my $finalGIFindex = $fileName2Number{$finalGIF};

	          my $lineNumberOnWhichThisVerseBegins = $chapterAndVerse2Info[$book][$chapter][$verse]{'lineNumberOnWhichThisVerseBegins'};

                  my $begShade = isDark($book,$chapter,$verse) ? "dark" : "light";
  		  # our ETL'd rows are zero-based but all the ScrollScraper logic is one-based
                  my $rowPlus1 = $lineNumberOnWhichThisVerseBegins + 1;
                  $verseInfo{"$firstGIF"}{"$chapter:$verse"} = "$begShade," .  $rowPlus1;

##                  my ($book,$chapterOfNextVerse,$verseOfNextVerse) = goForward($book,$chapter,$verse,1);
##	          my $lineNumberOnWhichFollowingVerseBegins = $chapterAndVerse2Info[$book][$chapterOfNextVerse][$verseOfNextVerse]{'lineNumberOnWhichThisVerseBegins'};
##	          my $rowPlus1 = $lineNumberOnWhichFollowingVerseBegins + 1;
##                  my $endShade = $begShade eq "light" ? "dark" : "light";
##
##                  $verseInfo{"$finalGIF"}{"$chapterOfNextVerse:$verseOfNextVerse"} = "$endShade," .  $rowPlus1;

	     }
	}
}

# Second of two passes through this data because we need to reference %verseInfo in the second pass
print "BOOK,CHAPTER,VERSE,FIRSTGIF,FINALGIF,LINENUMBERONWHICHTHISVERSEBEGINS,INDEXOFVERSESTARTPOSITIONONTHATLINE,STARTX,STARTY,ENDX,ENDY\n";
foreach my $book (1,2,3,4,5) {
	my $chaptersInBook = @{$versesPerChapter[$book-1]};
        my $verseInBook = -1; # zero-based count
	#	print "$book,$chaptersInBook\n";
	for (my $chapter=1; $chapter <= $chaptersInBook; $chapter++) {
	     my $versesInThisChapter = $versesPerChapter[$book-1][$chapter-1];
	     for (my $verse=1; $verse <= $versesInThisChapter; $verse++) {
                  $verseInBook++;
	          my %val = %{$chapterAndVerse2Info[$book][$chapter][$verse]};
	          my $firstGIF = $chapterAndVerse2Info[$book][$chapter][$verse]{'firstGIF'};
	          my $finalGIF = $chapterAndVerse2Info[$book][$chapter][$verse]{'finalGIF'};

	          my $firstGIFindex = $fileName2Number{$firstGIF};
	          my $finalGIFindex = $fileName2Number{$finalGIF};

	          my $lineNumberOnWhichThisVerseBegins = $chapterAndVerse2Info[$book][$chapter][$verse]{'lineNumberOnWhichThisVerseBegins'};

                  my $begShade = isDark($book,$chapter,$verse) ? "dark" : "light";
  		  # our ETL'd rows are zero-based but all the ScrollScraper logic is one-based
                  my $rowPlus1 = $lineNumberOnWhichThisVerseBegins + 1;
                  $verseInfo{"$firstGIF"}{"$chapter:$verse"} = "$begShade," .  $rowPlus1;

	          my $indexOfVerseStartPositionOnThatLine = $chapterAndVerse2Info[$book][$chapter][$verse]{'indexOfVerseStartPositionOnThatLine'};


	          my @begintags = tagTikkunRegionsByColorFromURL("$outputSite" . $firstGIF);
	          my @endtags = tagTikkunRegionsByColorFromURL("$outputSite" . $finalGIF);
                  my($startx,$endx,$starty,$endy);
          
	          if ($verseInfo{$firstGIF}{"$chapter:$verse"}) {
		          my ($begshade,$begrow) = split /,/,$verseInfo{$firstGIF}{"$chapter:$verse"};
		          for my $tag (@begintags) {
			          my($observedShade, $row1, $x1, $row2, $x2) = @{$tag};
			          if ($observedShade eq $begshade && $row1 eq $begrow) {
				          $x1 -= 5;
				          $x1 = 0 if $x1 < 0;
				          if ($row1 > 1 && $tag eq $begintags[0]) { # the first tag, but doesn't appear in the first row
					          $row1 = 1;
					          $x1 = 0;
				          }
          #				$begLabel = "$shadingDir/alpha_TOP" . "$row1" . "_" . "$x1" . ".png";
				          $startx = $x1;
				          $starty = (($row1 - 1) + $verseInBook) * $gifHeight;
				          last;
			          }
		          }
	          }
          
	          if ($verseInfo{$finalGIF}{"$chapter:$verse"}) {
                          my @sortedVerses = sort { compareChapterAndVerse($a,$b) }  keys %{$verseInfo{$finalGIF}};
                          my ($endshade,$endrow) = split /,/,$verseInfo{$finalGIF}{"$chapter:$verse"};
		          for my $tag (@endtags) {
			          my($observedShade, $row1, $x1, $row2, $x2) = @{$tag};
			          if ($sortedVerses[0] eq "$chapter:$verse") {
				          $x2 -= 0;
				          $x2 = 0 if $x2 < 0;
				          $x2 = $gifWidth if $x2 > ($gifWidth - 12);
				          if ($observedShade eq $endshade && $row1 eq $endrow) {
          #					$endLabel = "$shadingDir/alpha_BOT" . "$row2" . "_" . ($gifWidth-$x2) . ".png";
				                  $endx = ($gifWidth-$x2);
				                  $endy = (($row2 - 1) + $verseInBook) * $gifHeight;
					          last;
				          }
			          } else {
				          my ($theshade,$therow) = split /,/,$verseInfo{$finalGIF}{$sortedVerses[0]};
				          if ($observedShade eq $theshade && $row1 eq $therow) { # we've accounted for a verse with this shade
					          shift @sortedVerses;
				          }
			          }
		          }
	          } else { # we are finishing our verse which was started in the previous GIF (or perhaps even earlier)
		          my $tag = $endtags[0];
                          my $endshade = isDark($book,$chapter,$verse) ? "dark" : "light";
		          my($observedShade, $row1, $x1, $row2, $x2) = @{$tag};
		          for my $tag (@endtags) {
			          my($observedShade, $row1, $x1, $row2, $x2) = @{$tag};
			          $x2 -= 0;
			          $x2 = 0 if $x2 < 0;
			          $x2 = $gifWidth if $x2 > ($gifWidth - 12);
			          if ($observedShade eq $endshade) {
          #				$endLabel = "$shadingDir/alpha_BOT" . "$row2" . "_" . ($gifWidth-$x2) . ".png";
			                  $endx = ($gifWidth-$x2);
			                  $endy = (($row2 - 1) + $verseInBook) * $gifHeight;
				          last;
			          }
		          }
	          }


		  print "$book,$chapter,$verse,$firstGIF,$finalGIF,$lineNumberOnWhichThisVerseBegins,$indexOfVerseStartPositionOnThatLine,$startx,$starty,$endx,$endy\n";
	     }
	}
}


####

## TODO: I think I need to be doing something with finalGIF.   And perhaps bumping forward a verse
## so I can implicitly find the position of where that next verse begins, and thereby see where this
## verse ends

