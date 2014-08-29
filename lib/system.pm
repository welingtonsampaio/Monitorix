#
# Monitorix - A lightweight system monitoring tool.
#
# Copyright (C) 2005-2014 by Jordi Sanfeliu <jordi@fibranet.cat>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along
# with this program; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
#

package system;

use strict;
use warnings;
use Monitorix;
use RRDs;
use DBI();
use Exporter 'import';
our @EXPORT = qw(system_init system_update system_cgi);

sub system_init {
	my $myself = (caller(0))[3];
	my ($package, $config, $debug) = @_;
	my $rrd = $config->{base_lib} . $package . ".rrd";
	my $system = $config->{system};

	my $info;
	my @rra;
	my @tmp;
	my $n;

	my @average;
	my @min;
	my @max;
	my @last;

	#$config->{max_historic_years}

	# check dependencies
	if(lc($system->{alerts}->{loadavg_enabled}) eq "y") {
		if(! -x $system->{alerts}->{loadavg_script}) {
			logger("$myself: ERROR: script '$system->{alerts}->{loadavg_script}' doesn't exist or don't has execution permissions.");
		}
	}

	$config->{system_hist_alert1} = 0;
	push(@{$config->{func_update}}, $package);
	logger("$myself: Ok") if $debug;
}

sub system_update {
	my $myself = (caller(0))[3];
	my ($package, $config, $debug) = @_;
	my $system = $config->{system};

	my $load1 = 0;
	my $load5 = 0;
	my $load15 = 0;
	my $nproc = 0;
	my $npslp = 0;
	my $nprun = 0;
	my $npwio = 0;
	my $npzom = 0;
	my $npstp = 0;
	my $npswp = 0;
	my $mtotl = 0;
	my $mbuff = 0;
	my $mcach = 0;
	my $mfree = 0;
	my $macti = 0;
	my $minac = 0;
	my $val01 = 0;
	my $val02 = 0;
	my $val03 = 0;
	my $val04 = 0;
	my $val05 = 0;

	$npwio = $npzom = $npstp = $npswp = 0;

	if($config->{os} eq "Linux") {
		open(IN, "/proc/loadavg");
		while(<IN>) {
			if(/^(\d+\.\d+) (\d+\.\d+) (\d+\.\d+) (\d+)\/(\d+)/) {
				$load1 = $1;
				$load5 = $2;
				$load15 = $3;
				$nprun = $4;
				$npslp = $5;
			}
		}
		close(IN);
		$nproc = $npslp + $nprun;

		open(IN, "/proc/meminfo");
		while(<IN>) {
			if(/^MemTotal:\s+(\d+) kB$/) {
				$mtotl = $1;
				next;
			}
			if(/^MemFree:\s+(\d+) kB$/) {
				$mfree = $1;
				next;
			}
			if(/^Buffers:\s+(\d+) kB$/) {
				$mbuff = $1;
				next;
			}
			if(/^Cached:\s+(\d+) kB$/) {
				$mcach = $1;
				last;
			}
		}
		close(IN);
		$macti = $minac = "";
	}

	chomp(
		$load1,
		$load5,
		$load15,
		$nproc,
		$npslp,
		$nprun,
		$npwio,
		$npzom,
		$npstp,
		$npswp,
		$mtotl,
		$mbuff,
		$mcach,
		$mfree,
		$macti,
		$minac,
	);

	# SYSTEM alert
	if(lc($system->{alerts}->{loadavg_enabled}) eq "y") {
		if(!$system->{alerts}->{loadavg_threshold} || $load15 < $system->{alerts}->{loadavg_threshold}) {
			$config->{system_hist_alert1} = 0;
		} else {
			if(!$config->{system_hist_alert1}) {
				$config->{system_hist_alert1} = time;
			}
			if($config->{system_hist_alert1} > 0 && (time - $config->{system_hist_alert1}) >= $system->{alerts}->{loadavg_timeintvl}) {
				if(-x $system->{alerts}->{loadavg_script}) {
					logger("$myself: ALERT: executing script '$system->{alerts}->{loadavg_script}'.");
					system($system->{alerts}->{loadavg_script} . " " .$system->{alerts}->{loadavg_timeintvl} . " " . $system->{alerts}->{loadavg_threshold} . " " . $load15);
				} else {
					logger("$myself: ERROR: script '$system->{alerts}->{loadavg_script}' doesn't exist or don't has execution permissions.");
				}
				$config->{system_hist_alert1} = time;
			}
		}
	}

	my $dbh = DBI->connect("DBI:mysql:database=horus_monitoring;host=localhost",
                           "horus", "horus_password",
                           {'RaiseError' => 1});
    $dbh->do("INSERT INTO data VALUES (null, 'loadaverage',   YEAR(NOW()), MONTH(NOW()), DAY(NOW()), HOUR(NOW()), MINUTE(NOW()), SECOND(NOW()), " . $dbh->quote("$load1|$load5|$load15") . ")");
    $dbh->do("INSERT INTO data VALUES (null, 'memory',        YEAR(NOW()), MONTH(NOW()), DAY(NOW()), HOUR(NOW()), MINUTE(NOW()), SECOND(NOW()), " . $dbh->quote("$mtotl|$mbuff|$mcach|$mfree") . ")");
    $dbh->do("INSERT INTO data VALUES (null, 'proccesscount', YEAR(NOW()), MONTH(NOW()), DAY(NOW()), HOUR(NOW()), MINUTE(NOW()), SECOND(NOW()), " . $dbh->quote("$nproc|$npslp|$nprun") . ")");
    $dbh->disconnect();
}

sub system_cgi {
}

sub get_uptime {
	my $config = shift;
	my $str;
	my $uptime;

	if($config->{os} eq "Linux") {
		open(IN, "/proc/uptime");
		($uptime, undef) = split(' ', <IN>);
		close(IN);
	} elsif($config->{os} eq "FreeBSD") {
		open(IN, "/sbin/sysctl -n kern.boottime |");
		(undef, undef, undef, $uptime) = split(' ', <IN>);
		close(IN);
		$uptime =~ s/,//;
		$uptime = time - int($uptime);
	} elsif($config->{os} eq "OpenBSD" || $config->{os} eq "NetBSD") {
		open(IN, "/sbin/sysctl -n kern.boottime |");
		$uptime = <IN>;
		close(IN);
		chomp($uptime);
		$uptime = time - int($uptime);
	}

	return uptime2str($uptime);
}

1;
