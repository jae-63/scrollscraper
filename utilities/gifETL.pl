use strict;

use List::Util qw(min max);


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

# Note that each of the five books begin with a dark-blue verse, and then light-blue verses are alternated thereafter
sub isDark {
     my($book,$chapter,$verse) = @_;

     my $retval = 1;

     while ($chapter > 1 || $verse > 1) {
         my @results = goBack($book,$chapter,$verse,1);
         ($book,$chapter,$verse) = @results;
	 $retval = 1 - $retval;
     }

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

print "BOOK,CHAPTER,VERSE,FIRSTGIF,FINALGIF,LINENUMBERONWHICHTHISVERSEBEGINS,INDEXOFVERSESTARTPOSITIONONTHATLINE\n";
foreach my $book (1,2,3,4,5) {
	my $chaptersInBook = @{$versesPerChapter[$book-1]};
	#	print "$book,$chaptersInBook\n";
	for (my $chapter=1; $chapter <= $chaptersInBook; $chapter++) {
	     my $versesInThisChapter = $versesPerChapter[$book-1][$chapter-1];
	     for (my $verse=1; $verse <= $versesInThisChapter; $verse++) {
	          my %val = %{$chapterAndVerse2Info[$book][$chapter][$verse]};
	          my $firstGIF = $chapterAndVerse2Info[$book][$chapter][$verse]{'firstGIF'};
	          my $finalGIF = $chapterAndVerse2Info[$book][$chapter][$verse]{'finalGIF'};
	          my $lineNumberOnWhichThisVerseBegins = $chapterAndVerse2Info[$book][$chapter][$verse]{'lineNumberOnWhichThisVerseBegins'};
	          my $indexOfVerseStartPositionOnThatLine = $chapterAndVerse2Info[$book][$chapter][$verse]{'indexOfVerseStartPositionOnThatLine'};
		  print "$book,$chapter,$verse,$firstGIF,$finalGIF,$lineNumberOnWhichThisVerseBegins,$indexOfVerseStartPositionOnThatLine\n";
	     }
	}
}
