# TODO

- cleanup: use defaultdict(int) for counting dicts instead of foo[x] = foo.get(x, 0) + 1
	- not supported in python 2.4 - do any users use python 2.4?
	- debian lenny (oldstable) has python 2.5
- bug: multirepo tags
	- self.tags contains tags from all repos - WRONG

- general: analysis, ohloh-like?
	- age: active days / days - high % means active project usually
	- number of contributors (& their active days)

- https://sourceforge.net/tracker/index.php?func=detail&aid=2865754&group_id=203965&atid=987714
	- gitstats is a great tool, but the one thing that I miss is the number of
	SLOC or comments on the "lines of code" image. Could this somehow be
	added?

[Unsorted]
- clean up after running gnuplot (option to keep .dat files around?)
- show raw data in some way (the tables used currently aren't very nice)
- allow multiple stylesheets
	- parameter --style
	- styles/{default,...}.css
- could show some statistics from last year, month, etc... pisg-like?
- Commandline options
	--debug / --verbose
- save command line settings and use them next run if not overridden?

[Stats]
- General
	- Total repository size (slooooow)?

- Activity by Time?
	- (G?) Last 30 days
	- (G?) Last 12 months
	- (T) Hour of Week: percentages / coloring?
	- (G) Pace of Changes - number of line/other changes happening over time

- Authors
	- (T) List of authors
		- Lines
	- (T) Author of Month
		- Lines
	- (T) Author of Year
		- Lines

- Files
	- Average revisions per file
	- (G) Average file size: x = date, y = lines/file
	- (T) Largest Files?
	- (T) Files With Most Revisions?

- Lines
	- Average lines/file
	- (G) Lines of Code: show tags as vertical lines?

- Tags
	- Lines

- Author page for each author
	- Name, mail
	- Total commits (%)
	- LOC (%)
	- Last commit: date
	- First commit: date
	- Activity by Clock Time
		- (G) Hour of Day
		- (G) Day of Week
	- (T) Activity in Directories: Directory, Changes, LOC, LOC/change
	- (Most Recent Commits?)
	- Author of Month(s):
	- Author of Year(s):

- Pages for years?
	- Commits (% of all)
	- Author top ten
	- Month statistics
