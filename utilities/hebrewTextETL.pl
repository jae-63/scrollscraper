use strict;
use JSON::Parse 'read_json';

my $input = "data/entire_torah.json";


my $p = read_json ($input);

print "my \%verse2hebrew;\n";

foreach my $bookNum (0,1,2,3,4) {
    my %bookContents = %{@{$p}[$bookNum]};
    my @chapters = @{$bookContents{"chapter"}};
    my $chapterNum = 0;
    for my $chapter (@chapters) {
        $chapterNum++;
        my @verses = @{$chapter};
        my $dbg;
        my $verseNum = 0;
        for my $verse (@verses) {
          $verseNum++;
          my $key = sprintf("%02d%03d%03d",$bookNum+1,$chapterNum,$verseNum);
          print "\$verse2hebrew{\"$key\"} = \"$verse\";\n";
        }
    }
}
