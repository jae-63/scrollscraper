use strict;
use Data::Dumper;

my $verseLengthOfRandomSections = 10;

# Derived from bible.ort.org.   Note that both the King James bible and Machon Mamre differ from this!
my @fontSizeOverrides = (
    [ 2, 15, 1, 22, 0.8], # Song of the Sea, Exodus 15:1-22
    [ 5, 32, 1, 43, 0.9], # Haazinu, Deuteronomy 32:1-43
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

# my $chaptersInBook = ($versesPerChapter[ $book - 1 ]) + 1;

my @selections;
push @selections,[2,15,1+rand()*20]; # Song of Sea
push @selections,[5,32,1+rand()*40]; # Haazinu
push @selections,[rand(5)+1,1,rand(3)]; # one random near the beginning of a book

my $book = int(rand(5)) + 1; # random book for selection near end of that book
#my $chaptersInBook = $versesPerChapter[ $book - 1 ];
my $chaptersInBook = @{ $versesPerChapter[ $book - 1 ] };
$chaptersInBook;
push @selections,[$book,$chaptersInBook-1,$versesPerChapter[$book-1][$chaptersInBook-1]-2-rand(5)];

for (my $i = 0; $i < 7; $i++) {
    my $book = int(rand(5)) + 1;
    my $chaptersInBook = @{ $versesPerChapter[ $book - 1 ] };
    $chaptersInBook;
    my $chapter = int(rand($chaptersInBook)+1);
    my $verse = rand($versesPerChapter[$book-1][$chapter-1]) + 1;
    push @selections,[$book,$chapter,$verse];
}

my $dbg;

for my $selection (@selections) {
    my @selection = @{$selection};
    reportSelection(int($selection[0]),int($selection[1]),int($selection[2]));
}

my $dbg;


sub reportSelection {
    my ( $book, $startc, $startv ) = @_;

    my $len = int(rand($verseLengthOfRandomSections)) + 1;
    my($discard_book,$endc,$endv) = goForward($book,$startc,$startv,$len);

    print "Book $book, $startc:$startv to $endc:$endv\n";
    print "<ul>\n";
    my($extra,$moreextra,$name);
    for (my $j=0; $j < 3; $j++) {
        if ($j == 0) {
            $extra = "";
            $moreextra = "";
            $name = "legacy";
        } elsif ($j == 1) {
            $extra = "2";
            $moreextra = "";
            $name = "new,shaded";
        } elsif ($j == 2) {
            $extra = "2";
            $moreextra = "&trueTypeFonts=1";
            $name = "trueType,shaded";
        }
        my $ref="https://scrollscraper.adatshalom.net/scrollscraper${extra}.cgi?book=$book&startc=$startc&startv=$startv&endc=$endc&endv=$endv&doShading=1&dontUseCache=1${moreextra}";
        print "<li><a target=_blank href=\"$ref\">$name</a></li>\n";
     }
     print "</ul>\n";
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
