use strict;
use GD;

my $ortGifWidth = 445;
my $ortGifHeight = 90;
my $ortGifRows = 3;

my $ortGifHeightPerRow = $ortGifHeight / $ortGifRows;

my $verticalFudgeFactor = 5;

my $dir = "./ScrollScraperalphaPNGs";

foreach my $val ("TOP","BOT") {
	for (my $row = 1; $row <= $ortGifRows ; $row++) {
		for (my $x = $ortGifWidth; $x >= 0; $x--) {
			my $fname = "$dir/alpha_$val" . $row . "_" . $x . ".png";
			open PNG,">$fname" or die "Unable to open output file $fname";
			binmode PNG;
			my $image = GD::Image->new($ortGifWidth,$ortGifHeight);
			$image->saveAlpha(1);
			$image->alphaBlending(0);
			my $transparent = $image->colorAllocateAlpha(255,255,255,127);
			my $translucent= $image->colorAllocateAlpha(53,53,53,40);
			$image->filledRectangle(0,0,$ortGifWidth,$ortGifHeight,$transparent);
			if ($val eq "TOP") {
				$image->filledRectangle(0,0,$ortGifWidth,$ortGifHeightPerRow*($row-1)-$verticalFudgeFactor,$translucent);
				$image->filledRectangle($ortGifWidth-$x,$ortGifHeightPerRow*($row-1)-$verticalFudgeFactor,$ortGifWidth,$ortGifHeightPerRow*$row,$translucent);
			} else {
				$image->filledRectangle(0,$ortGifHeightPerRow*$row+$verticalFudgeFactor,$ortGifWidth,$ortGifHeight,$translucent);
				$image->filledRectangle(0,$ortGifHeightPerRow*($row-1)+$verticalFudgeFactor,$x,30*$row+$verticalFudgeFactor,$translucent);
			}
			$image->alphaBlending(1);
			print PNG $image->png;
			close PNG;
		}
	}
}
