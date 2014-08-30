#!/usr/bin/env perl
use strict;
use warnings;
use FindBin qw($Bin);
use lib $Bin . "/lib", "/usr/lib/monitorix";

use Monitorix;
use CGI qw(:standard);
use Config::General;
use POSIX;
use DBI();

my $dbh = DBI->connect('DBI:mysql:{{dbname}};host={{dbhost}}', '{{dbuser}}', '{{dbpass}}',
	            { RaiseError => 1 }
	           );
print '{';
print '"loadaverage": [';
my $sth = $dbh->prepare('SELECT year,month,day,hour,minute,value FROM loadaverage');
$sth->execute();
my ( $year, $month, $day, $hour, $minute, $value);
while ( ($year, $month, $day, $hour, $minute, $value) = $sth->fetchrow_array( ) )  {
         print '{"date": "'."$day\/$month\/$year $hour:$minute:00".'", "value": "'.$value.'"}';
}
print ']';
$sth->finish();
print '}';
$dbh->disconnect();

0;
