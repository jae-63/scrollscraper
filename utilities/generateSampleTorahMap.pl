use strict;
use GD;

my $ortGifWidth = 445;
my $ortGifHeight = 90;
my $ortGifRows = 3;

my $ortGifHeightPerRow = $ortGifHeight / $ortGifRows;

my $verticalFudgeFactor = 5;

binmode STDOUT;
my $image = GD::Image->new($ortGifWidth,$ortGifHeight);

my $translucentLightBlue = $image->colorAllocateAlpha(132,132,255,40);
my $translucentDarkBlue = $image->colorAllocateAlpha(100,46,201,40);
my $translucentNone = $image->colorAllocateAlpha(53,53,53,40);

while (<>) {
    my @fields   = split /,/;
    my $filename = shift @fields;
    my $row      = shift @fields;
    my @localMapInfo;
    while ( $#fields >= 0 ) {
        my $drawingColor;
        my $startx  = shift @fields;
        my $endx    = shift @fields;
        my $color   = shift @fields;
        my $chapter = shift @fields;
        my $verse   = shift @fields;
        push @localMapInfo, [ $startx, $endx, $color, $chapter, $verse ];
        if ($color eq "dark") {
           $drawingColor = $translucentDarkBlue;
        } elsif ($color eq "light") {
           $drawingColor = $translucentLightBlue;
        } else {
           $drawingColor = $translucentNone;
        }
#	$image->filledRectangle(0,0,$ortGifWidth,$ortGifHeightPerRow*($row-1)-$verticalFudgeFactor,$drawingColor);
	$image->filledRectangle($ortGifWidth-$startx,$ortGifHeightPerRow*($row-1)-$verticalFudgeFactor,$ortGifWidth-$endx,$ortGifHeightPerRow*$row,$drawingColor);
    }
}
$image->alphaBlending(1);
print STDOUT $image->png;
