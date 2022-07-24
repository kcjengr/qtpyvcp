#
# Regular cron jobs for the qtpyvcp package
#
0 4	* * *	root	[ -x /usr/bin/qtpyvcp_maintenance ] && /usr/bin/qtpyvcp_maintenance
