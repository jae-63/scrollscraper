use strict;
use GD;

my $dir = "./ScrollScraperalphaPNGs";

foreach my $val ("TOP","BOT") {
	for (my $row = 1; $row <=3 ; $row++) {
		for (my $x = 445; $x >= 0; $x--) {
			my $fname = "$dir/alpha_$val" . $row . "_" . $x . ".png";
			open PNG,">$fname" or die "Unable to open output file $fname";
			binmode PNG;
			my $image = GD::Image->new(445,90);
			$image->saveAlpha(1);
			$image->alphaBlending(0);
			my $transparent = $image->colorAllocateAlpha(255,255,255,127);
			my $translucent= $image->colorAllocateAlpha(53,53,53,40);
			$image->filledRectangle(0,0,445,90,$transparent);
			if ($val eq "TOP") {
				$image->filledRectangle(0,0,445,30*($row-1)-5,$translucent);
				$image->filledRectangle(445-$x,30*($row-1)-5,445,30*$row,$translucent);
			} else {
				$image->filledRectangle(0,30*$row+5,445,90,$translucent);
				$image->filledRectangle(0,30*($row-1)+5,$x,30*$row+5,$translucent);
			}
			$image->alphaBlending(1);
			print PNG $image->png;
			close PNG;
		}
	}
}
	
