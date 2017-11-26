#!/usr/bin/perl
use Fcntl ':flock'; # import LOCK_* constants
use CGI;

my $qDir = "/home/jepstein/mp3Creation/queue";
my $lame = "/home/jepstein/lame-3.97/frontend/lame"; # use "lame" for WAV->MP3 conversion
my $sox = "/home/jepstein/mplayerExperiments/sox-13.0.0/src/sox";
# public-domain sox-based concatenation From: http://www.boutell.com/scripts/catwav.html
## #!/bin/sh
## sox $1 -r 44100 -c 2 -s -w /tmp/$$-1.raw
## sox $2 -r 44100 -c 2 -s -w /tmp/$$-2.raw
## cat /tmp/$$-1.raw /tmp/$$-2.raw > /tmp/$$.raw
## sox -r 44100 -c 2 -s -w /tmp/$$.raw $3
## rm /tmp/$$*.raw
my $festivalSpeechSynthesis = "/home/jepstein/festival/festival/bin/text2wave";
my $festivalOptions = "-scale 3 -o";
my $mplayer = "/home/jepstein/mplayerExperiments/MPlayer-1.0rc1/mplayer"; # use for RealAudio->Wav conversion
my $raUrlFormat = "http://bible.ort.org/webmedia/t%d/%s.ra";
my $spacerShortRaw = "/home/jepstein/mplayerExperiments/spacershort.raw";
my $spacerLongRaw = "/home/jepstein/mplayerExperiments/spacerlong.raw";
my $smilbase = "./smil/";
my $mainURL = "http://scrollscraper.adatshalom.net";

my @englishBookNames = ("Genesis","Exodus","Leviticus","Numbers","Deuteronomy");

my $dayStampFile = "./smil/daystampAndLock.txt";
my $ipDatabase = "./smil/ipdatabase";

# parameters to be obtained via CGI; @raFiles should be split// from a text string
my ($book,@raFiles,$audioRepeatCount,$startc,$startv,$endc,$endv,$flags);
#  $book=1;
#  @raFiles = ( "0101","0102","0103","0104" );
#  $audioRepeatCount = 3;
#  $startc = 1;
#  $startv = 1;
#  $endc = 1;
#  $endv = 4;
#  $flags = 3;



my $q = new CGI;
if ($q->param('book')) {
	print "Content-type: text/html\n\n";

	foreach my $key ($q->param) {
		if ($q->param($key) !~ /^[0-9,]+$/ && $q->param($key) !~ /^(on|off)$/) {
			my $str = "Invalid parameter: $key=" . $q->param($key);
			print "$str\n";
			die "$str";
		}
	}

	$book = $q->param('book');
	my $raFiles = $q->param('raFiles');
	$startc = $q->param('startc');
	$startv = $q->param('startv');
	$endc = $q->param('endc');
	$endv = $q->param('endv');
	$audioRepeatCount = $q->param('audioRepeatCount') if $q->param('audioRepeatCount');
	@raFiles = split /,/,$raFiles;
}

$audioRepeatCount = 1 unless $audioRepeatCount;
$audioRepeatCount = 9 unless $audioRepeatCount < 9;

my $audioFileName = rangeToFileName($smilbase, $book,$startc,$startv,$endc,$endv,$flags,$audioRepeatCount) . "REC.mp3";
if ( -f $audioFileName && ! -z $audioFileName && -f "$audioFileName.COMPLETED") {
	print "Your MP3 file was previously created, and appears at:<BR>\n";

	#
	# update the actual MP3 file's timestamp to show this access attempt, but leave the
	# timestamp of $audioFileName.COMPLETED unchanged.  This way we can keep track of
	# both dates, and use them both to determine which older MP3 files should be culled.
	#
	utime undef,undef,$audioFileName;

	$_ = $audioFileName;
	s/^\.//;
	my $link = "$mainURL$_";
	print "<a href=\"$link\">$link</a>\n";
	exit 0;
}

my ($retval,$info) = accessPermitted($ENV{'REMOTE_ADDR'},$dayStampFile,$ipDatabase,($#raFiles+1),$audioRepeatCount);
if ($retval == 0) {
	print STDERR "MP3 creation access denied: $info\n";
	print "MP3 creation access denied: $info\n";
	exit 1;
}

my $tmpdir = "/tmp/$$.mp3.scrollscraper";

my $effortRequired = ($#raFiles+1) * $audioRepeatCount;
my $scriptfname = $ENV{"REMOTE_ADDR"} . "_" . $effortRequired . "_" . "$$.sh";
open THESCRIPT,">$qDir/$scriptfname" or die "Unable to open output file $qDir/$scriptfname";
print "Your output MP3 file will appear at:<BR>\n";
$_ = $audioFileName;
s/^\.//;
my $link = "$mainURL$_";
print "<a href=\"$link\">$link</a>\n";


# generate speech synthesis
my $tts = "This is an excerpt from " . getBookName($book) . ", Chapter $startc, "; # it would be nice to include the Parsha, but the pronounciation is too poor
if ($startc != $endc) {
	$tts .= "verse $startv through chapter $endc verse $endv.";
} else {
	$tts .= "verses $startv through $endv.";
}

$tts .= "  The following recorded materials are copyright world-ORT, 1997, all rights reserved.";
my $wavFileName = "$tmpdir/synthesizedSpeech.wav";

print THESCRIPT "#!/bin/sh\n\nonint ()\n{\n\trm -rf $tmpdir\n\texit 1\n}\n\n";
print THESCRIPT "trap onint SIGINT\ntrap onint SIGQUIT\ntrap onint SIGTERM\ntrap onint SIGPIPE\n\n";
print THESCRIPT "/bin/touch $audioFileName.STARTED\n";
print THESCRIPT "queuedTime=" . `/bin/date +%s` . "\n";
print THESCRIPT "queuedTimeFmted=" . `/bin/date` . "\n";
print THESCRIPT "startTime=`/bin/date +%s`\n";
print THESCRIPT "startTimeFmted=`/bin/date`\n";
print THESCRIPT "mkdir $tmpdir\n";
print THESCRIPT "/bin/echo \"<br>\" `/bin/date` \"Beginning processing of $scriptfname\"\n";

print THESCRIPT "/bin/echo \"$tts\" | $festivalSpeechSynthesis $festivalOptions $wavFileName\n";
print THESCRIPT "$sox $wavFileName -r 44100 -c 2 -s -w $tmpdir/synthesizedSpeech.raw >/dev/null\n";


my $catList = "";
foreach my $raFile (@raFiles) {
	my $url = sprintf $raUrlFormat,$book,$raFile;
	print THESCRIPT "$mplayer $url -ao pcm:file=$tmpdir/$raFile.wav >/dev/null\n";
	print THESCRIPT "$sox $tmpdir/$raFile.wav -r 44100 -c 2 -s -w $tmpdir/$raFile.raw >/dev/null\n";
	$catList .= " $tmpdir/$raFile.raw";
}
print THESCRIPT "cat$catList >$tmpdir/reading.raw\n";
my $catList2 = "";
for (my $i = 0; $i < $audioRepeatCount; $i++) {
	$catList2 .= " $spacerLongRaw" unless ($i == 0);
	$catList2 .= " $tmpdir/reading.raw";
}

print THESCRIPT "cat";
print THESCRIPT " $tmpdir/synthesizedSpeech.raw $spacerShortRaw";
print THESCRIPT "$catList2 >$tmpdir/aggregate.raw\n";
print THESCRIPT "/bin/echo \"<br>\" `/bin/date` 'Preparing conversion of concatenated raw->wav'\n";
print THESCRIPT "$sox -r 44100 -c 2 -s -w $tmpdir/aggregate.raw $tmpdir/aggregate.wav >/dev/null\n";
print THESCRIPT "/bin/echo \"<br>\" `/bin/date` 'Preparing conversion of concatenated wav->mp3'\n";
print THESCRIPT "nice $lame -h --silent --scale 2 $tmpdir/aggregate.wav $audioFileName >/dev/null\n";
print THESCRIPT "/bin/echo \"<br>\" `/bin/date` 'Processing complete!'\n";
print THESCRIPT "/bin/touch $audioFileName.COMPLETED\n";
print THESCRIPT "/bin/rm -f $audioFileName.STARTED\n";
print THESCRIPT "/bin/rm -rf $tmpdir\n";
print THESCRIPT "endTime=`/bin/date +%s`\n";
print THESCRIPT "endTimeFmted=`/bin/date`\n";
print THESCRIPT "/bin/echo 'Queued time: ' `expr \$startTime - \$queuedTime`\n";
print THESCRIPT "/bin/echo 'Running time: ' `expr \$endTime - \$startTime`\n";
close THESCRIPT;

# temporary: to be replaced by queueing system:
system("/bin/sh $qDir/$scriptfname");
my($dev,$ino,$mode,$nlink,$uid,$gid,$rdev,$size, $atime,$lastMtime,$ctime,$blksize,$blocks) = stat($audioFileName);
recordFileSize($size,$ENV{'REMOTE_ADDR'},$dayStampFile,$ipDatabase);


sub rangeToFileName {
	my ($cachebase, $book,$startc,$startv,$endc,$endv,$flags,$audioRepeatCount) = @_;

	my $dir = "$cachebase/$book.$startc";
	$audioRepeatCount = 1 unless defined $audioRepeatCount;
	my $file = "$startv.$endc.$endv.$flags.$audioRepeatCount";

	system("mkdir -p $dir");
	return "$dir/$file";
}

sub getBookName {
	my($book,$inHebrew) = @_;

#	return $hebrewBookNames[$book-1] if $inHebrew;
	return $englishBookNames[$book-1];
}


#
# is access permitted to this resource?   Restrictions are on a per-day basis.
# Each IP address is permitted $perIpPerDayLimit accesses per day.  This is
# subject to a global constraint of a total of $globalLimit access per day, from
# all remote IP addresses combined.
#
sub accessPermitted {
	my ($ip,$dayStampFile,$ipDatabase,$numVerses,$repeatCount) = @_;
	my $lastMtimeStamp = 0;
	my %accessesToday;

	my $perIpPerDayLimit = 8;
	my $perIpPerDayDiskLimit = 30 * 1024 * 1024;
	my $globalLimit = 100;
	my $globalDiskLimit =  300 * 1024 * 1024;
	my $maxVerses = 72;
	my $retString = "";

	my($sec,$min,$hour,$mday,$mon,$year,$wday,$yday,$isdst) = localtime(time);
	my $dayStamp = $year * 1000 + $yday;

	return (0,"MP3 creation temporarily unavailable as of 7 April 2009; sorry for the inconvenience");
	return (0,"(# verses) * (audio repeat count) = $numVerses * $repeatCount > $maxVerses") if(($numVerses * $repeatCount) > $maxVerses);

	if (-f $ipDatabase) {
		my($dev,$ino,$mode,$nlink,$uid,$gid,$rdev,$size, $atime,$lastMtime,$ctime,$blksize,$blocks) = stat(_);
		
		my($sec,$min,$hour,$mday,$mon,$year,$wday,$yday,$isdst) = localtime($lastMtime);
		$lastMtimeStamp = $year * 1000 + $yday;
	}
#	print "lastMtimeStamp: $lastMtimeStamp, file: $dayStampFile\n";

	open DAYSTAMPFILE,"+<",$dayStampFile or return (0,"Unable to open $dayStampFile");
	flock (DAYSTAMPFILE,LOCK_EX);

	if ($lastMtimeStamp < $dayStamp) { # it's no longer the same day as when the last access was made
		print STDERR "Removing $ipDatabase, timestamps: ($lastMtimeStamp,$dayStamp)\n";
		unlink ($ipDatabase); # or maybe just truncate it??
	}

	dbmopen(%accessesToday,$ipDatabase,0666);

	my $globalAccessCount = $accessesToday{"TOTAL"};
	my $newval = $accessesToday{$ip};

	my $globalDiskUsed = $accessesToday{"DISK_TOTAL"};
	my $myDiskUsed = $accessesToday{"DISK_" . $ip};

	if ($globalAccessCount >= $globalLimit) {
		$retString .= "Daily global access limit $globalLimit exceeded\n";
	}
	if ($newval >= $perIpPerDayLimit) {
		$retString .= "Daily limit ($perIpPerDayLimit) exceeded for IP $ip\n";
	}
	if ($globalDiskUsed >= $globalDiskLimit) {
		$retString .= "Daily global disk space quota $globalDiskLimit exceeded\n";
	}
	if ($myDiskUsed >= $perIpPerDayDiskLimit) {
		$retString .= "Daily disk quota ($perIpPerDayDiskLimit) exceeded for IP $ip\n";
	}

	unless ($retString) {
		$accessesToday{"TOTAL"}++;
		$accessesToday{$ip}++;
		$newval++;
		$globalAccessCount++;
	}

	dbmclose(%accessesToday);
#	print "Accesses from this IP address so far today: $newval\n";

	flock (DAYSTAMPFILE,LOCK_UN);
	close (DAYSTAMPFILE);

	if ($retString) {
		return (0,$retString);
	} else {
		return (1,"Access $newval granted for $ip, $globalAccessCount accesses so far today\n");
	}
}

sub recordFileSize {
	my ($size,$ip,$dayStampFile,$ipDatabase) = @_;
	my %accessesToday;

	open DAYSTAMPFILE,"+<",$dayStampFile or return;
	flock (DAYSTAMPFILE,LOCK_EX);
	dbmopen(%accessesToday,$ipDatabase,0666);
	$accessesToday{"DISK_TOTAL"} += $size;
	$accessesToday{"DISK_" . $ip} += $size;
	dbmclose(%accessesToday);

	flock (DAYSTAMPFILE,LOCK_UN);
	close (DAYSTAMPFILE);
}



