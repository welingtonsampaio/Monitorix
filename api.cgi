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
	my ($table, $sth, $reverse) = @_;
	my $more = 0;
	my $content = '';
	my ( $year, $month, $day, $hour, $minute, $value);
	print '[';
	while ( ($year, $month, $day, $hour, $minute, $value) = $sth->fetchrow_array( ) )  {
		if ($day < 10)    { $day = "0".$day; }
		if ($month < 10)  { $month = "0".$month; }
		if ($hour < 10)   { $hour = "0".$hour; }
		if ($minute < 10) { $minute = "0".$minute; }
		if ( $reverse == 1 ) {
			if ($more == 1){
				$content = ',' . $content;
			}
			$content = '{"date": "'."$year-$month-$day $hour:$minute:00".'", "value": "'.$value.'"}' . $content;
		}else{
			if ($more == 1){
				$content = $content . ',';
			}
			$content = $content . '{"date": "'."$year-$month-$day $hour:$minute:00".'", "value": "'.$value.'"}';
		}
		$more = 1;
	}
	print $content;
	print '] ';
	$sth->finish();
}

sub print_yesterday {
	my ($table, $dbh) = @_;
	my $epoc = time();
	$epoc = $epoc - 24 * 60 * 60;
	my ($sec, $min, $hour, $mday, $mon, $year) = localtime($epoc);
	$year += 1900;
	$mon += 1;
	my $sth = query_results($table, "year = $year AND month = $mon AND day = $mday", $dbh);
	print_results($table, $sth, 0);
}

sub print_day {
	my ($table, $dbh) = @_;
	my ($sec,$min,$hour,$mday,$mon,$year,$wday,$yday,$isdst) = localtime();
	my $ontem= $mday - 1;
	my $sth = query_results($table, "year = $year AND month = $mon AND day = $mday", $dbh);
	print_results($table, $sth, 0);
}

sub print_hour {
  my ($table, $dbh) = @_;
  my ($sec,$min,$hour,$mday,$mon,$year,$wday,$yday,$isdst) = localtime();
	$year += 1900;
	$mon += 1;
  my $sth = query_results($table, "year = $year AND month = $mon AND day = $mday ORDER BY id DESC LIMIT 60", $dbh);
  print_results($table, $sth, 1);
}

sub print_current {
  my ($table, $dbh) = @_;
  my ($sec,$min,$hour,$mday,$mon,$year,$wday,$yday,$isdst) = localtime();
	$year += 1900;
	$mon += 1;
  my $sth = query_results($table, "year = $year AND month = $mon AND day = $mday ORDER BY id DESC LIMIT 1", $dbh);
  print_results($table, $sth, 0);
}

our $mode = defined(param('mode')) ? param('mode') : 'loadaverage';
our $time = defined(param('time')) ? param('time') : 'today';

if ( $mode eq "loadaverage" ) {
	if ($time eq 'yesterday') {
		print_yesterday('loadaverage', $dbh);
	} elsif ( $time eq 'today' ) {
		print_day('loadaverage', $dbh);
	} elsif ( $time eq 'hour' ) {
    print_hour('loadaverage', $dbh);
  } elsif ( $time eq 'current' ) {
		print_current('loadaverage', $dbh);
	}
}

if ( $mode eq "memory" ) {
	if ($time eq 'yesterday') {
    print_yesterday('memory', $dbh);
	} elsif ( $time eq 'today' ) {
    print_day('memory', $dbh);
  } elsif ( $time eq 'hour' ) {
    print_hour('memory', $dbh);
  } elsif ( $time eq 'current' ) {
    print_current('memory', $dbh);
	}
}

if ( $mode eq "proccess_count" ) {
	print_day('proccess_count', $dbh);
}


if ( $mode eq "cpu_info" ) {
	if ($time eq 'yesterday') {
		print_yesterday('cpu_info', $dbh);
	} elsif ( $time eq 'today' ) {
		print_day('cpu_info', $dbh);
	} elsif ( $time eq 'hour' ) {
		print_hour('cpu_info', $dbh);
	} elsif ( $time eq 'current' ) {
		print_current('cpu_info', $dbh);
	}
}


$dbh->disconnect();

0;
