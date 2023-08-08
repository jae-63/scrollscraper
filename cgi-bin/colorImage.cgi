#!/usr/bin/perl
#
# Recolor a bible.ort.org Tikkin "training-text" GIF, by manipulating its colormap.
#
use strict;
use CGI;
use GD;
use LWP::Simple;

# bible.ort.org images (used in ScrollScraper) have RGB colors:
#    light blue = 132/132/255
#    dark blue  = 100/46/201

my @colors = ( "132/132/255", "100/46/201" );

my $baseURL = "http://bible.ort.org/"
  ; # hard-code this to avoid people use this as a way to arbitary recode any GIF on the Internet

my $usage =
    "Usage: " 
  . $0
  . " gif-relative-to-bible-ort-org-webmedia comma-delimited-coloring";

my $q = new CGI;
my ( $thegif, $coloring );
my @coloring;

#open MYLOG,">/tmp/jaelog.txt";
#print MYLOG "Opening log\n";
if ( $q->param('thegif') ) {
    print "Content-type: image/gif\n\n";

    #print MYLOG "Writing content-type to stdout\n";
    $thegif   = $q->param('thegif');
    $coloring = $q->param('coloring');
}
else {
    $thegif   = shift or die $usage;
    $coloring = shift or die $usage;
}
@coloring = split /,/, $coloring;
my $theurl = $baseURL . $thegif;
my $gifdata = get($theurl) or die "Unable to download $theurl";

my $image = GD::Image->newFromGifData($gifdata);

if ( $coloring[0] eq 'shade' ) {
    if ($coloring[1] == 1) {
	    my %color;
	    my %count;
	    my %colorHash;
	    $color{'light'} = $image->colorAllocate( 132, 132, 255 );
	    $color{'dark'}  = $image->colorAllocate( 100, 46,  201 );
	    $color{'NONE'}  = $image->colorAllocate( 0, 0, 0 );

	    for (my $x = 0; $x < 445; $x++) {
		    for (my $y = 0; $y < 90; $y++) {

                    	my $index = $image->getPixel( $x, $y ) ;
                    	unless ( defined( $colorHash{$index} ) ) {
                        	$colorHash{$index} = determineColor( $index, \@colors );
			}
			$image->setPixel($x,$y,$color{$colorHash{$index}});
			$count{$colorHash{$index}}++;
		     }
	     }
	     foreach (keys %count) {
		     print STDERR $_ . ":" . $count{$_} . "\n";
	     }
    }
    else {

	  # TODO: perhaps extract more parameters from the other elements of @coloring ?
	    my @regions = tagTikkunRegionsByColor($gifdata);

	    my %color;
	    $color{'light'} = $image->colorAllocate( 132, 132, 255 );
	    $color{'dark'}  = $image->colorAllocate( 100, 46,  201 );


	    for my $region (@regions) {
	        my ( $shade, $srow, $sx, $erow, $ex ) = @{$region};
	        print STDERR join( ',', @{$region} ) . "\n";
	        $sx = 445 - $sx;    # switch to left-to-right coordinates
	        $ex = 445 - $ex;
	        if ( $srow == $erow ) {
	            $image->filledRectangle( $ex, $srow * 30, $sx, $srow * 30 + 5,
	                $color{$shade} );
	        }
	        else {
	            $image->filledRectangle( 0, $srow * 30, $sx, $srow * 30 + 5,
	                $color{$shade} );
	            $image->filledRectangle( $ex, $erow * 30, 445, $erow * 30 + 5,
	                $color{$shade} );
	            $image->filledRectangle( 0, 1 * 30, 445, 1 * 30 + 5,
	                $color{$shade} )
	              if ( ( $erow - $srow ) >= 2 );
	        }
	    }
    }
}
else {
    my %alreadyModified;
    
    foreach my $color (@colors) {
        my @arr = split /\//,$color;
        my @thecoloring = ();
        for my $elem (@arr) {
    	push @thecoloring,shift @coloring;
        }
        #print MYLOG "Coloring: " . join(";",@thecoloring) . "\n";
        my $colorIndex;
        while ($colorIndex = $image->colorClosest(@arr)) {
    	last if $alreadyModified{$colorIndex};
            my @RGB = $image->rgb($colorIndex);
            last if notClose(5400,\@arr,\@RGB);
    	$alreadyModified{$colorIndex}++;
            $image->colorDeallocate($colorIndex);
            my $index = $image->colorAllocate(@thecoloring);
        }
        my $dbg;
    }
}

#print MYLOG "Ready to output gif\n";
#close MYLOG;
binmode STDOUT;
print $image->gif;

# measure color proximity in terms of Euclidean-distance in the three-dimensional RGB space
sub notClose {
    my ( $thresh, $aR1, $aR2 ) = @_;
    my @a1 = @{$aR1};
    my @a2 = @{$aR2};
    my $dist =
      ( $a1[0] - $a2[0] )**2 + ( $a1[1] - $a2[1] )**2 + ( $a1[2] - $a2[2] )**2;
    return $dist >
      $thresh;    # 5400 corresponds to a distance of ~70, since 70*70 = 4900
}

# TODO: this function is very unreliable as of 7/30/09
sub tagTikkunRegionsByColorFromURL {
    my ($theurl) = @_;

    my $gifdata = get($theurl) or die "Unable to download $theurl";

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

    my $width = 445;
    my $image = GD::Image->newFromGifData($gifdata);

    my $lastColor = 'NONE';
    my ( $startrow,  $startx )  = ( 0, 0 );
    my ( $recentrow, $recentx ) = ( 0, 0 );
    my $lastIteration;

    my $samplingRow = 9;

    my @rgb;    # define it out here for debugging ease

    for ( my $row = 0, my $y = $samplingRow ; $row <= 2 ; $row++, $y += 30 ) {

        for ( my $x = 0 ; $x < $width ; $x++ ) {
            $lastIteration = 1 if $row == 2 && $x == ( $width - 1 );

            my $index =
              $image->getPixel( $width - $x, $y );    # TODO: off-by-one errors?
            unless ( defined( $colorHash{$index} ) ) {
                $colorHash{$index} = determineColor( $index, \@colors );
                my $dbg;
            }
            my $theColor = $colorHash{$index};

            if ( $theColor eq 'NONE' ) {

                #search vertically
                for ( my $y2 = $row*30 ; $y2 < $row*30+30 ; $y2++ ) {
                    my $index = $image->getPixel( $width - $x, $y2 )
                      ;                               # TODO: off-by-one errors?
                    unless ( defined( $colorHash{$index} ) ) {
                        $colorHash{$index} = determineColor( $index, \@colors );
                    }
                    if ( $colorHash{$index} ne 'NONE' ) {
                        $theColor = $colorHash{$index};
                        last;
                    }
                }
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
                        $colorHash{$index} = determineColor( $index, \@colors );
                    }
                    $votes{ $colorHash{$index} }++;
                }
                if ( $votes{$theColor} > 3 && $votes{$theColor} > 1.2 * $votes{$lastColor} ) {
                    my @res =
                      ( $lastColor, $startrow, $startx, $recentrow, $recentx );
                    push @retval, [@res];

                    $lastColor = $theColor;
                    $startrow  = $row;
                    $startx    = $x;
                }
            }
            $recentrow = $row;
            $recentx   = $x;
        }
    }

    return @retval;

}

sub determineColor {
    my ( $index, $aRefColors ) = @_;
    my @colors = @{$aRefColors};
    my $retval;

    my @rgb   = $image->rgb($index);
    my $shade = 'light';
    foreach my $color (@colors) {    # for each of our two colors
        my @arr = split /\//, $color;
        unless ( notClose( 5400, \@arr, \@rgb ) ) {
            $retval = $shade;
            last;
        }
        $shade = 'dark';             # for 2nd time through this two-color loop
    }
    $retval = 'NONE' unless defined($retval);
    return $retval;
}


