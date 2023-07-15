use strict;

use List::Util qw(min max);
use GD;
use LWP::Simple;

my $gifWidth     = 445;
my $gifRowHeight = 30;

my %mapInfo;
my %fileName2Number;
my $fileNameNumber   = 0;
my @filenames;
my $smallestRowLength = $gifWidth * 2;

while (<>) {
	chomp;
        my @fields   = split /,/;
        my $filename = shift @fields;
        my $row      = shift @fields;
        if ( $row == 0 ) {
            push @filenames, $filename;
            $fileName2Number{$filename} = $fileNameNumber++;
        }
        my @localMapInfo;
        my $totalRowLength = 0;

        while ( $#fields >= 0 ) {
            my $startx  = shift @fields;
            my $endx    = shift @fields;
            my $color   = shift @fields;
            my $chapter = shift @fields;
            my $verse   = shift @fields;
	    $totalRowLength += $endx - $startx + 1;
            push @localMapInfo, [ $startx, $endx, $color, $chapter, $verse ];
        }
        $mapInfo{$filename}{$row} = \@localMapInfo;
        $smallestRowLength = min($smallestRowLength,$totalRowLength);
	print "$filename,$row,$totalRowLength\n";
}

print "SMALLEST ROW LENGTH: $smallestRowLength\n";
