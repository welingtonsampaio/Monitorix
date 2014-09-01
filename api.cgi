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

sub query_results {
	my ($table, $where, $dbh) = @_;
	my $sth = $dbh->prepare("SELECT year,month,day,hour,minute,value FROM $table WHERE $where");
	$sth->execute();
	return $sth;
}

sub print_results {
	my ($table, $sth) = @_;
	my $more = 0;
	my ( $year, $month, $day, $hour, $minute, $value);
	print '"'. $table .'": [';
	while ( ($year, $month, $day, $hour, $minute, $value) = $sth->fetchrow_array( ) )  {
		if ($more == 1){
			print ', ';
		}
		print '{"date": "'."$day\/$month\/$year $hour:$minute:00".'", "value": "'.$value.'"}';
		$more = 1;
	}
	print '] ';
	$sth->finish();
}

sub print_day {
	my ($table, $dbh) = @_;
	my ($sec,$min,$hour,$mday,$mon,$year,$wday,$yday,$isdst) = localtime();
	my $ontem= $mday - 1;
	my $sth = query_results($table, "day = $mday", $dbh);
	print_results($table, $sth);
}


our $mode = defined(param('mode')) ? param('mode') : 'loadaverage';

print '{';

if ( $mode eq "loadaverage" ) {
	print_day('loadaverage', $dbh);
}

if ( $mode eq "memory" ) {
	print_day('memory', $dbh);
}

if ( $mode eq "proccess_count" ) {
	print_day('proccess_count', $dbh);
}


print '}';
$dbh->disconnect();

0;
