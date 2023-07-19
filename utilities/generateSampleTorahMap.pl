use strict;
use GD;

my $ortGifWidth = 445;
my $ortGifHeight = 90;
my $ortGifRows = 3;

my $ortGifHeightPerRow = $ortGifHeight / $ortGifRows;

my $verticalFudgeFactor = 5;
my $verticalFudgeFactor = 0;
my $verticalFontFudgeFactor = 20;

binmode STDOUT;
my $image = GD::Image->new($ortGifWidth,$ortGifHeight);

my $translucentBlackWriting = $image->colorAllocateAlpha(0,0,0,255);
my $translucentLightBlue = $image->colorAllocateAlpha(132,132,255,1);
my $translucentDarkBlue = $image->colorAllocateAlpha(100,46,201,1);
my $translucentNone = $image->colorAllocateAlpha(200,200,200,1);

my $transparent = $image->colorAllocateAlpha(255,255,255,127);

$image->filledRectangle(0,0,$ortGifWidth,$ortGifHeight,$transparent);

while (<>) {
    chomp;
    my @fields   = split /,/;
    my $filename = shift @fields;
    my $row      = shift @fields;
    $row++;
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
printf STDERR "$row:%d,%d,%d,%d,%s\n",$ortGifWidth-$startx,$ortGifHeightPerRow*($row-1)-$verticalFudgeFactor,$ortGifWidth-$endx,$ortGifHeightPerRow*$row,$color;
#	$image->filledRectangle(0,0,$ortGifWidth,$ortGifHeightPerRow*($row-1)-$verticalFudgeFactor,$drawingColor);
	$image->filledRectangle($ortGifWidth-$startx,$ortGifHeightPerRow*($row-1)-$verticalFudgeFactor,$ortGifWidth-$endx,$ortGifHeightPerRow*$row,$drawingColor);
	$image->string(gdLargeFont,$ortGifWidth-$endx,$ortGifHeightPerRow*$row-$verticalFontFudgeFactor,"$chapter:$verse",$translucentBlackWriting) if ($color ne "NONE");
    }
}
$image->alphaBlending(1);
print STDOUT $image->png;
