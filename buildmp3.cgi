#!/usr/bin/perl
use Fcntl ':flock'; # import LOCK_* constants
use CGI;

# set environment vars to make gtts-cli happy
$ENV{'LC_ALL'}='C.UTF-8';
$ENV{'LANG'}='C.UTF-8';

my $qDir = "/home/ec2-user/scrollscraperWorkingDir";
my $qDir = "./scrollscraperWorkingDir" if $ENV{"IS_DOCKER"};
# my $lame = "/home/jepstein/lame-3.97/frontend/lame"; # use "lame" for WAV->MP3 conversion
# my $sox = "/home/jepstein/mplayerExperiments/sox-13.0.0/src/sox";
# public-domain sox-based concatenation From: http://www.boutell.com/scripts/catwav.html
## #!/bin/sh
## sox $1 -r 44100 -c 2 -s -w /tmp/$$-1.raw
## sox $2 -r 44100 -c 2 -s -w /tmp/$$-2.raw
## cat /tmp/$$-1.raw /tmp/$$-2.raw > /tmp/$$.raw
## sox -r 44100 -c 2 -s -w /tmp/$$.raw $3
## rm /tmp/$$*.raw
# my $festivalSpeechSynthesis = "/home/jepstein/festival/festival/bin/text2wave";
# my $festivalOptions = "-scale 3 -o";
my $gttsCli = "/usr/local/bin/gtts-cli";
my $gttsCli = "gtts-cli" if $ENV{"IS_DOCKER"};
my $ffmpeg = "/home/ec2-user/ffmpeg-3.4-64bit-static/ffmpeg";
my $mp3wrap = "mp3wrap";
# my $mplayer = "/home/jepstein/mplayerExperiments/MPlayer-1.0rc1/mplayer"; # use for RealAudio->Wav conversion
# my $raUrlFormat = "http://bible.ort.org/webmedia/t%d/%s.ra";
my $mp3UrlFormat = "http://bible.ort.org/webmedia/t%d/%s.mp3";
# my $spacerShortRaw = "/home/jepstein/mplayerExperiments/spacershort.raw";
# my $spacerLongRaw = "/home/jepstein/mplayerExperiments/spacerlong.raw";
my $spacerShortMp3 = "./spacershort.mp3";
my $spacerLongMp3 = "./spacerlong.mp3";
my $ortMp3BaseDir = "/srv/www/scrollscraper.adatshalom.net/public_html/ORT_MP3s.recoded";
# The following is a mount point to use with Docker
my $ortMp3BaseDir = "/ort_mp3s" if $ENV{"IS_DOCKER"};
my $smilBase = "./smil/";
my $smilBase = "/state/smil/" if $ENV{"IS_DOCKER"};
my $mainURL = "http://scrollscraper.adatshalom.net";

my @englishBookNames = ("Genesis","Exodus","Leviticus","Numbers","Deuteronomy");

my $maxFetches = 200; # safety valve;

# Derived from bible.ort.org.   Note that both the King James bible and Machon Mamre differ from this!
my @versesPerChapter = (
[31,25,24,26,32,22,24,22,29,32,32,20,18,24,21,17,27,33,38,18,34,24,20,67,34,35,46,22,35,43,54,33,20,31,29,43,36,30,23,23,57,38,34,34,28,34,31,22,33,26],
[22,25,22,31,23,30,29,28,35,29,10,51,22,31,27,36,16,27,25,23,37,30,33,18,40,37,21,43,46,38,18,35,23,35,35,38,29,31,43],
[17,16,17,35,26,23,38,36,24,20,47,8,59,57,33,34,16,30,37,27,24,33,44,23,55,46,34],
[54,34,51,49,31,27,89,26,23,36,35,16,33,45,41,35,28,32,22,29,35,41,30,25,18,65,23,31,39,17,54,42,56,29,34,13],
[46,37,29,49,30,25,26,20,29,22,32,31,19,29,23,22,20,22,21,20,23,29,26,22,19,19,26,69,28,20,30,52,29,12],
);


my $dayStampFile = "$smilBase/daystampAndLock.txt";
my $ipDatabase = "$smilBase/ipdatabase";

# parameters to be obtained via CGI; @raFiles should be split// from a text string
my ($book,@raFiles,$audioRepeatCount,$startc,$startv,$endc,$endv,$flags,$httpStyle);
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
	print "Content-type: text/html\n\n" unless $q->param('httpStyle');

	foreach my $key ($q->param) {
		if ($q->param($key) && $q->param($key) !~ /^[0-9,]+$/ && $q->param($key) !~ /^(on|off)$/) {
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
	$httpStyle = $q->param('httpStyle');
	$audioRepeatCount = $q->param('audioRepeatCount') if $q->param('audioRepeatCount');
	@raFiles = split /,/,$raFiles;
}

$audioRepeatCount = 1 unless $audioRepeatCount;
$audioRepeatCount = 9 unless $audioRepeatCount < 9;

# Compute the list of audio verses rather than obtaining it explicitly from the command line
unless (@raFiles) {
        my $chaptersInBook = $versesPerChapter[$book-1] + 1;
        my $v = $startv;
        my $c = $startc;
        my $count = 0;
        $audioList = "";

        while ($count++ < $maxFetches) {
                $audioList .= "," if ($count > 1);
                $audioList .= sprintf "%02d%02d",$c,$v;
                last if ($c >= $endc && $v >= $endv);
                $v++;
                if ($v > $versesPerChapter[$book-1][$c-1]) {
                        $v = 1;
                        $c++;
                        last if $c >= $chaptersInBook;
                }
        }
	@raFiles = split /,/,$audioList;
#        print STDERR "Audiolist: $audioList\n";
}

my $audioFileName = rangeToFileName($smilBase, $book,$startc,$startv,$endc,$endv,$flags,$audioRepeatCount) . "REC.mp3";
if ( -f $audioFileName && ! -z $audioFileName && -f "$audioFileName.COMPLETED") {
	#
	# update the actual MP3 file's timestamp to show this access attempt, but leave the
	# timestamp of $audioFileName.COMPLETED unchanged.  This way we can keep track of
	# both dates, and use them both to determine which older MP3 files should be culled.
	#
	utime undef,undef,$audioFileName;

	$_ = $audioFileName;
	s/^\.//;
	my $link = "$mainURL$_";
        if ($httpStyle) {
                print "HTTP/1.1 302 Found\n";
		print "Location: $link\n";
        } else {
		print "Your MP3 file was previously created, and appears at:<BR>\n";
		print "<a href=\"$link\">$link</a>\n";
        }

	exit 0;
}

my ($retval,$info) = accessPermitted($ENV{'REMOTE_ADDR'},$dayStampFile,$ipDatabase,($#raFiles+1),$audioRepeatCount);
if ($retval == 0) {
        if ($httpStyle) {
                print "HTTP/1.1 429 Too Many Requests\n";
		print <<EOF
Content-Type: text/html
Retry-After: 43200

<html>
  <head>
    <title>Too Many Requests</title>
  </head>
  <body>
    <h1>Too Many Requests</h1>
    <p>There are daily limits on this Web site</p>
    <p>$info</p>
  </body>
</html>
EOF
	} else {
		print STDERR "MP3 creation access denied: $info\n";
		print "MP3 creation access denied: $info\n";
	}
	exit 1;
}

my $tmpdir = "/tmp/$$.mp3.scrollscraper";

my $effortRequired = ($#raFiles+1) * $audioRepeatCount;
my $scriptfname = $ENV{"REMOTE_ADDR"} . "_" . $effortRequired . "_" . "$$.sh";
open THESCRIPT,">$qDir/$scriptfname" or die "Unable to open output file $qDir/$scriptfname";
if ($httpStyle) {
        print "HTTP/1.1 202 Accepted\n";
} else {
	print "Your output MP3 file will appear at:<BR>\n";
	$_ = $audioFileName;
	s/^\.//;
	my $link = "$mainURL$_";
	print "<a href=\"$link\">$link</a>\n";
}


# generate speech synthesis
my $tts = "This is an excerpt from " . getBookName($book) . ", Chapter $startc, "; # it would be nice to include the Parsha, but the pronounciation is too poor
if ($startc != $endc) {
	$tts .= "verse $startv through chapter $endc verse $endv.";
} else {
	$tts .= "verses $startv through $endv.";
}

$tts .= "  The following recorded materials are copyright world-ORT, nineteen-ninety-seven, all rights reserved.";
my $ttsFileName = "$tmpdir/synthesizedSpeech.mp3";

# Sample gtts-cli usage:
#   gtts-cli "hello" -o /tmp/hello.mp3

print THESCRIPT "#!/bin/sh\n\nonint ()\n{\n\trm -rf $tmpdir\n\texit 1\n}\n\n";
print THESCRIPT "trap onint INT\ntrap onint QUIT\ntrap onint TERM\ntrap onint PIPE\n\n";
print THESCRIPT "/bin/touch $audioFileName.STARTED\n";
print THESCRIPT "queuedTime=" . `/bin/date +%s` . "\n";
my $fmtedTime = `/bin/date`;
chomp $fmtedTime;
print THESCRIPT "queuedTimeFmted=\"$fmtedTime\"\n";
print THESCRIPT "startTime=`/bin/date +%s`\n";
print THESCRIPT "startTimeFmted=`/bin/date`\n";
print THESCRIPT "mkdir $tmpdir\n";
print THESCRIPT "/bin/echo \"<br>\" `/bin/date` \"Beginning processing of $scriptfname\"\n";

print THESCRIPT "LC_ALL=C.UTF-8 LANG=C.UTF-8 $gttsCli \"$tts\" -o $ttsFileName\n";
# print THESCRIPT "$sox $ttsFileName -r 44100 -c 2 -s -w $tmpdir/synthesizedSpeech.raw >/dev/null\n";

my $thisDir=`pwd`;
chomp $thisDir;


my $catList = "";
# Historically these were RealAudio ("ra") files, so for backwards compatability let's retain the older parameter name
foreach my $raFile (@raFiles) {
	my $url = sprintf $mp3UrlFormat,$book,$raFile;
	print THESCRIPT "cp $ortMp3BaseDir/t$book/$raFile.mp3 $tmpdir/$raFile.mp3 2>/dev/null\n";
#	print THESCRIPT "wget $url -O $tmpdir/$raFile.mp3 2>/dev/null\n";
# 	print THESCRIPT "$sox $tmpdir/$raFile.wav -r 44100 -c 2 -s -w $tmpdir/$raFile.raw >/dev/null\n";
        if ($catList) {
            $catList .= " ";
        }
	$catList .= "$tmpdir/$raFile.mp3";
}
print THESCRIPT "(cd $tmpdir; $mp3wrap reading $catList)\n";
my $catList2 = "";
for (my $i = 0; $i < $audioRepeatCount; $i++) {
	$catList2 .= " $thisDir/$spacerLongMp3" unless ($i == 0);
	$catList2 .= " $tmpdir/reading_MP3WRAP.mp3";
}

print THESCRIPT "(cd $tmpdir; $mp3wrap aggregate $ttsFileName $thisDir/$spacerShortMp3 $catList2)\n";
# print THESCRIPT "/bin/echo \"<br>\" `/bin/date` 'Preparing conversion of concatenated raw->wav'\n";
# print THESCRIPT "$sox -r 44100 -c 2 -s -w $tmpdir/aggregate.raw $tmpdir/aggregate.wav >/dev/null\n";
# print THESCRIPT "/bin/echo \"<br>\" `/bin/date` 'Preparing conversion of concatenated wav->mp3'\n";
# print THESCRIPT "nice $lame -h --silent --scale 2 $tmpdir/aggregate.wav $audioFileName >/dev/null\n";
print THESCRIPT "cp -p $tmpdir/aggregate_MP3WRAP.mp3 $audioFileName\n";
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
	my $globalLimit = 1000;
	my $globalDiskLimit =  300 * 1024 * 1024;
	my $maxVerses = 72;
	my $retString = "";

	my($sec,$min,$hour,$mday,$mon,$year,$wday,$yday,$isdst) = localtime(time);
	my $dayStamp = $year * 1000 + $yday;

#	return (0,"MP3 creation temporarily unavailable as of 7 April 2009; sorry for the inconvenience");
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
	if (defined($globalDiskUsed) && $globalDiskUsed >= $globalDiskLimit) {
		$retString .= "Daily global disk space quota $globalDiskLimit exceeded, current usage $globalDiskUsed\n";
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


