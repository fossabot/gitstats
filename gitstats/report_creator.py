# Copyright (c) 2007-2014 Heikki Hokkanen <hoxu@users.sf.net> & others contributors
# GPLv2 / GPLv3
# Copyright (c) 2024-present Xianpeng Shen <xianpeng.shen@gmail.com>.
# GPLv2 / GPLv3
import os
import glob
import shutil
import datetime
import time
from gitstats import load_config, GNUPLOT_COMMON, WEEKDAYS
from gitstats.utils import (
    get_version,
    get_git_version,
    get_gnuplot_version,
    get_pipe_output,
    gnuplot_cmd,
)

conf = load_config()


class ReportCreator:
    """Creates the actual report based on given data."""

    def __init__(self):
        self.data = None
        self.path = None

    def create(self, data, path):
        self.data = data
        self.path = path


class HTMLReportCreator(ReportCreator):
    def create(self, data, path):
        ReportCreator.create(self, data, path)
        self.title = data.project_name

        # copy static files to the report directory
        basedir = os.path.dirname(os.path.abspath(__file__))
        for file in (
            conf["style"],
            "sortable.js",
            "arrow-up.gif",
            "arrow-down.gif",
            "arrow-none.gif",
        ):
            src = basedir + "/" + file
            if os.path.exists(src):
                shutil.copyfile(src, path + "/" + file)
                break

        self.create_index_html(data, path)
        self.create_activity_html(data, path)
        self.create_authors_html(data, path)
        self.create_files_html(data, path)
        self.create_lines_html(data, path)
        self.create_tags_html(data, path)
        self.create_graphs(path)

    def create_index_html(self, data, path):
        f = open(path + "/index.html", "w")
        format = "%Y-%m-%d %H:%M:%S"
        self.print_header(f)

        f.write("<h1>GitStats - %s</h1>" % data.project_name)

        self.print_nav(f)

        f.write(html_header(2, "Git Overview"))

        f.write("<table border='1' cellspacing='0' cellpadding='4'>")
        f.write("<tr><td><b>Project name</b></td><td>%s</td></tr>" % data.project_name)
        f.write(
            "<tr><td><b>Generated</b></td><td>%s (in %d seconds)</td></tr>"
            % (
                datetime.datetime.now().strftime(format),
                time.time() - data.get_stamp_created(),
            )
        )
        f.write(
            '<tr><td><b>Generator</b></td><td><a href="https://github.com/shenxianpeng/gitstats">gitstats</a> %s, %s, %s</td></tr>'
            % (get_version(), get_git_version(), get_gnuplot_version())
        )
        f.write(
            "<tr><td><b>Report Period</b></td><td>%s to %s</td></tr>"
            % (
                data.get_first_commit_date().strftime(format),
                data.get_last_commit_date().strftime(format),
            )
        )
        f.write(
            "<tr><td><b>Age</b></td><td>%d days, %d active days (%3.2f%%)</td></tr>"
            % (
                data.get_commit_delta_days(),
                len(data.get_active_days()),
                (100.0 * len(data.get_active_days()) / data.get_commit_delta_days()),
            )
        )
        f.write(
            "<tr><td><b>Total Files</b></td><td>%s</td></tr>" % data.get_total_files()
        )
        f.write(
            "<tr><td><b>Total Lines of Code</b></td><td>%s (%d added, %d removed)</td></tr>"
            % (data.get_total_loc(), data.total_lines_added, data.total_lines_removed)
        )
        f.write(
            "<tr><td><b>Total Commits</b></td><td>%s (average %.1f commits per active day, %.1f per all days)</td></tr>"
            % (
                data.get_total_commits(),
                float(data.get_total_commits()) / len(data.get_active_days()),
                float(data.get_total_commits()) / data.get_commit_delta_days(),
            )
        )
        f.write(
            "<tr><td><b>Authors</b></td><td>%s (average %.1f commits per author)</td></tr>"
            % (
                data.get_total_authors(),
                (1.0 * data.get_total_commits()) / data.get_total_authors(),
            )
        )
        f.write("</table>")

        f.write("</body>\n</html>")
        f.close()

    def create_activity_html(self, data, path):
        ###
        # Activity
        f = open(path + "/activity.html", "w")
        self.print_header(f)
        f.write("<h1>Activity</h1>")
        self.print_nav(f)

        # f.write('<h2>Last 30 days</h2>')

        # f.write('<h2>Last 12 months</h2>')

        # Weekly activity
        WEEKS = 32
        f.write(html_header(2, "Weekly activity"))
        f.write("<p>Last %d weeks</p>" % WEEKS)

        # generate weeks to show (previous N weeks from now)
        now = datetime.datetime.now()
        deltaweek = datetime.timedelta(7)
        weeks = []
        stampcur = now
        for i in range(0, WEEKS):
            weeks.insert(0, stampcur.strftime("%Y-%W"))
            stampcur -= deltaweek

        # top row: commits & bar
        f.write('<table class="noborders"><tr>')
        for i in range(0, WEEKS):
            commits = 0
            if weeks[i] in data.activity_by_year_week:
                commits = data.activity_by_year_week[weeks[i]]

            percentage = 0
            if weeks[i] in data.activity_by_year_week:
                percentage = (
                    float(data.activity_by_year_week[weeks[i]])
                    / data.activity_by_year_week_peak
                )
            height = max(1, int(200 * percentage))
            f.write(
                '<td style="text-align: center; vertical-align: bottom">%d<div style="display: block; background-color: red; width: 20px; height: %dpx"></div></td>'
                % (commits, height)
            )

        # bottom row: year/week
        f.write("</tr><tr>")
        for i in range(0, WEEKS):
            f.write("<td>%s</td>" % (WEEKS - i))
        f.write("</tr></table>")

        # Hour of Day
        f.write(html_header(2, "Hour of Day"))
        hour_of_day = data.get_activity_by_hour_of_day()
        f.write("<table><tr><th>Hour</th>")
        for i in range(0, 24):
            f.write("<th>%d</th>" % i)
        f.write("</tr>\n<tr><th>Commits</th>")
        fp = open(path + "/hour_of_day.dat", "w")
        for i in range(0, 24):
            if i in hour_of_day:
                r = 127 + int(
                    (float(hour_of_day[i]) / data.activity_by_hour_of_day_busiest) * 128
                )
                f.write(
                    '<td style="background-color: rgb(%d, 0, 0)">%d</td>'
                    % (r, hour_of_day[i])
                )
                fp.write("%d %d\n" % (i, hour_of_day[i]))
            else:
                f.write("<td>0</td>")
                fp.write("%d 0\n" % i)
        fp.close()
        f.write("</tr>\n<tr><th>%</th>")
        totalcommits = data.get_total_commits()
        for i in range(0, 24):
            if i in hour_of_day:
                r = 127 + int(
                    (float(hour_of_day[i]) / data.activity_by_hour_of_day_busiest) * 128
                )
                f.write(
                    '<td style="background-color: rgb(%d, 0, 0)">%.2f</td>'
                    % (r, (100.0 * hour_of_day[i]) / totalcommits)
                )
            else:
                f.write("<td>0.00</td>")
        f.write("</tr></table>")
        f.write('<img src="hour_of_day.png" alt="Hour of Day">')
        fg = open(path + "/hour_of_day.dat", "w")
        for i in range(0, 24):
            if i in hour_of_day:
                fg.write("%d %d\n" % (i + 1, hour_of_day[i]))
            else:
                fg.write("%d 0\n" % (i + 1))
        fg.close()

        # Day of Week
        f.write(html_header(2, "Day of Week"))
        day_of_week = data.get_activity_by_day_of_week()
        f.write('<div class="vtable"><table>')
        f.write("<tr><th>Day</th><th>Total (%)</th></tr>")
        fp = open(path + "/day_of_week.dat", "w")
        for d in range(0, 7):
            commits = 0
            if d in day_of_week:
                commits = day_of_week[d]
            fp.write("%d %s %d\n" % (d + 1, WEEKDAYS[d], commits))
            f.write("<tr>")
            f.write("<th>%s</th>" % (WEEKDAYS[d]))
            if d in day_of_week:
                f.write(
                    "<td>%d (%.2f%%)</td>"
                    % (day_of_week[d], (100.0 * day_of_week[d]) / totalcommits)
                )
            else:
                f.write("<td>0</td>")
            f.write("</tr>")
        f.write("</table></div>")
        f.write('<img src="day_of_week.png" alt="Day of Week">')
        fp.close()

        # Hour of Week
        f.write(html_header(2, "Hour of Week"))
        f.write("<table>")

        f.write("<tr><th>Weekday</th>")
        for hour in range(0, 24):
            f.write("<th>%d</th>" % (hour))
        f.write("</tr>")

        for weekday in range(0, 7):
            f.write("<tr><th>%s</th>" % (WEEKDAYS[weekday]))
            for hour in range(0, 24):
                try:
                    commits = data.activity_by_hour_of_week[weekday][hour]
                except KeyError:
                    commits = 0
                if commits != 0:
                    f.write("<td")
                    r = 127 + int(
                        (float(commits) / data.activity_by_hour_of_week_busiest) * 128
                    )
                    f.write(' style="background-color: rgb(%d, 0, 0)"' % r)
                    f.write(">%d</td>" % commits)
                else:
                    f.write("<td></td>")
            f.write("</tr>")

        f.write("</table>")

        # Month of Year
        f.write(html_header(2, "Month of Year"))
        f.write('<div class="vtable"><table>')
        f.write("<tr><th>Month</th><th>Commits (%)</th></tr>")
        fp = open(path + "/month_of_year.dat", "w")
        for mm in range(1, 13):
            commits = 0
            if mm in data.activity_by_month_of_year:
                commits = data.activity_by_month_of_year[mm]
            f.write(
                "<tr><td>%d</td><td>%d (%.2f %%)</td></tr>"
                % (mm, commits, (100.0 * commits) / data.get_total_commits())
            )
            fp.write("%d %d\n" % (mm, commits))
        fp.close()
        f.write("</table></div>")
        f.write('<img src="month_of_year.png" alt="Month of Year">')

        # Commits by year/month
        f.write(html_header(2, "Commits by year/month"))
        f.write(
            '<div class="vtable"><table><tr><th>Month</th><th>Commits</th><th>Lines added</th><th>Lines removed</th></tr>'
        )
        for yymm in reversed(sorted(data.commits_by_month.keys())):
            f.write(
                "<tr><td>%s</td><td>%d</td><td>%d</td><td>%d</td></tr>"
                % (
                    yymm,
                    data.commits_by_month.get(yymm, 0),
                    data.lines_added_by_month.get(yymm, 0),
                    data.lines_removed_by_month.get(yymm, 0),
                )
            )
        f.write("</table></div>")
        f.write('<img src="commits_by_year_month.png" alt="Commits by year/month">')
        fg = open(path + "/commits_by_year_month.dat", "w")
        for yymm in sorted(data.commits_by_month.keys()):
            fg.write("%s %s\n" % (yymm, data.commits_by_month[yymm]))
        fg.close()

        # Commits by year
        f.write(html_header(2, "Commits by Year"))
        f.write(
            '<div class="vtable"><table><tr><th>Year</th><th>Commits (% of all)</th><th>Lines added</th><th>Lines removed</th></tr>'
        )
        for yy in reversed(sorted(data.commits_by_year.keys())):
            f.write(
                "<tr><td>%s</td><td>%d (%.2f%%)</td><td>%d</td><td>%d</td></tr>"
                % (
                    yy,
                    data.commits_by_year.get(yy, 0),
                    (100.0 * data.commits_by_year.get(yy, 0))
                    / data.get_total_commits(),
                    data.lines_added_by_year.get(yy, 0),
                    data.lines_removed_by_year.get(yy, 0),
                )
            )
        f.write("</table></div>")
        f.write('<img src="commits_by_year.png" alt="Commits by Year">')
        fg = open(path + "/commits_by_year.dat", "w")
        for yy in sorted(data.commits_by_year.keys()):
            fg.write("%d %d\n" % (yy, data.commits_by_year[yy]))
        fg.close()

        # Commits by timezone
        f.write(html_header(2, "Commits by Timezone"))
        f.write("<table><tr>")
        f.write("<th>Timezone</th><th>Commits</th>")
        f.write("</tr>")
        max_commits_on_tz = max(data.commits_by_timezone.values())
        for i in sorted(list(data.commits_by_timezone.keys()), key=lambda n: int(n)):
            commits = data.commits_by_timezone[i]
            r = 127 + int((float(commits) / max_commits_on_tz) * 128)
            f.write(
                '<tr><th>%s</th><td style="background-color: rgb(%d, 0, 0)">%d</td></tr>'
                % (i, r, commits)
            )
        f.write("</table>")

        f.write("</body></html>")
        f.close()

    def create_authors_html(self, data, path):
        ###
        # Authors
        f = open(path + "/authors.html", "w")
        self.print_header(f)

        f.write("<h1>Authors</h1>")
        self.print_nav(f)

        # Authors :: List of authors
        f.write(html_header(2, "List of Authors"))

        f.write('<table class="authors sortable" id="authors">')
        f.write(
            '<tr><th>Author</th><th>Commits (%)</th><th>+ lines</th><th>- lines</th><th>First commit</th><th>Last commit</th><th class="unsortable">Age</th><th>Active days</th><th># by commits</th></tr>'
        )
        for author in data.get_authors(conf["max_authors"]):
            info = data.get_author_info(author)
            f.write(
                "<tr><td>%s</td><td>%d (%.2f%%)</td><td>%d</td><td>%d</td><td>%s</td><td>%s</td><td>%s</td><td>%d</td><td>%d</td></tr>"
                % (
                    author,
                    info["commits"],
                    info["commits_frac"],
                    info["lines_added"],
                    info["lines_removed"],
                    info["date_first"],
                    info["date_last"],
                    info["timedelta"],
                    len(info["active_days"]),
                    info["place_by_commits"],
                )
            )
        f.write("</table>")

        allauthors = data.get_authors()
        if len(allauthors) > conf["max_authors"]:
            rest = allauthors[conf["max_authors"] :]
            f.write(
                '<p class="moreauthors">These didn\'t make it to the top: %s</p>'
                % ", ".join(rest)
            )

        f.write(html_header(2, "Cumulated Added Lines of Code per Author"))
        f.write(
            '<img src="lines_of_code_by_author.png" alt="Lines of code per Author">'
        )
        if len(allauthors) > conf["max_authors"]:
            f.write(
                '<p class="moreauthors">Only top %d authors shown</p>'
                % conf["max_authors"]
            )

        f.write(html_header(2, "Commits per Author"))
        f.write('<img src="commits_by_author.png" alt="Commits per Author">')
        if len(allauthors) > conf["max_authors"]:
            f.write(
                '<p class="moreauthors">Only top %d authors shown</p>'
                % conf["max_authors"]
            )

        fgl = open(path + "/lines_of_code_by_author.dat", "w")
        fgc = open(path + "/commits_by_author.dat", "w")

        lines_by_authors = {}  # cumulated added lines by
        # author. to save memory,
        # changes_by_date_by_author[stamp][author] is defined
        # only at points where author commits.
        # lines_by_authors allows us to generate all the
        # points in the .dat file.

        # Don't rely on get_authors to give the same order each
        # time. Be robust and keep the list in a variable.
        commits_by_authors = {}  # cumulated added lines by

        self.authors_to_plot = data.get_authors(conf["max_authors"])
        for author in self.authors_to_plot:
            lines_by_authors[author] = 0
            commits_by_authors[author] = 0
        for stamp in sorted(data.changes_by_date_by_author.keys()):
            fgl.write("%d" % stamp)
            fgc.write("%d" % stamp)
            for author in self.authors_to_plot:
                if author in list(data.changes_by_date_by_author[stamp].keys()):
                    lines_by_authors[author] = data.changes_by_date_by_author[stamp][
                        author
                    ]["lines_added"]
                    commits_by_authors[author] = data.changes_by_date_by_author[stamp][
                        author
                    ]["commits"]
                fgl.write(" %d" % lines_by_authors[author])
                fgc.write(" %d" % commits_by_authors[author])
            fgl.write("\n")
            fgc.write("\n")
        fgl.close()
        fgc.close()

        # Authors :: Author of Month
        f.write(html_header(2, "Author of Month"))
        f.write('<table class="sortable" id="aom">')
        f.write(
            '<tr><th>Month</th><th>Author</th><th>Commits (%%)</th><th class="unsortable">Next top %d</th><th>Number of authors</th></tr>'
            % conf["authors_top"]
        )
        for yymm in reversed(sorted(data.author_of_month.keys())):
            author_dict = data.author_of_month[yymm]
            authors = get_keys_sorted_by_values(author_dict)
            authors.reverse()
            commits = data.author_of_month[yymm][authors[0]]
            authors_str = ", ".join(authors[1 : conf["authors_top"] + 1])
            f.write(
                "<tr><td>%s</td><td>%s</td><td>%d (%.2f%% of %d)</td><td>%s</td><td>%d</td></tr>"
                % (
                    yymm,
                    authors[0],
                    commits,
                    (100.0 * commits) / data.commits_by_month[yymm],
                    data.commits_by_month[yymm],
                    authors_str,
                    len(authors),
                )
            )

        f.write("</table>")

        f.write(html_header(2, "Author of Year"))
        f.write(
            '<table class="sortable" id="aoy"><tr><th>Year</th><th>Author</th><th>Commits (%%)</th><th class="unsortable">Next top %d</th><th>Number of authors</th></tr>'
            % conf["authors_top"]
        )
        for yy in reversed(sorted(data.author_of_year.keys())):
            author_dict = data.author_of_year[yy]
            authors = get_keys_sorted_by_values(author_dict)
            authors.reverse()
            commits = data.author_of_year[yy][authors[0]]
            authors_str = ", ".join(authors[1 : conf["authors_top"] + 1])
            f.write(
                "<tr><td>%s</td><td>%s</td><td>%d (%.2f%% of %d)</td><td>%s</td><td>%d</td></tr>"
                % (
                    yy,
                    authors[0],
                    commits,
                    (100.0 * commits) / data.commits_by_year[yy],
                    data.commits_by_year[yy],
                    authors_str,
                    len(authors),
                )
            )
        f.write("</table>")

        # Domains
        f.write(html_header(2, "Commits by Domains"))
        domains_by_commits = get_keys_sorted_by_value_key(data.domains, "commits")
        domains_by_commits.reverse()  # most first
        f.write('<div class="vtable"><table>')
        f.write("<tr><th>Domains</th><th>Total (%)</th></tr>")
        fp = open(path + "/domains.dat", "w")
        n = 0
        for domain in domains_by_commits:
            if n == conf["max_domains"]:
                break
            commits = 0
            n += 1
            info = data.get_domain_info(domain)
            fp.write("%s %d %d\n" % (domain, n, info["commits"]))
            f.write(
                "<tr><th>%s</th><td>%d (%.2f%%)</td></tr>"
                % (
                    domain,
                    info["commits"],
                    (100.0 * info["commits"] / data.get_total_commits()),
                )
            )
        f.write("</table></div>")
        f.write('<img src="domains.png" alt="Commits by Domains">')
        fp.close()

        f.write("</body></html>")
        f.close()

    def create_files_html(self, data, path):
        ###
        # Files
        f = open(path + "/files.html", "w")
        self.print_header(f)
        f.write("<h1>Files</h1>")
        self.print_nav(f)

        f.write("<dl>\n")
        f.write("<dt>Total files</dt><dd>%d</dd>" % data.get_total_files())
        f.write("<dt>Total lines</dt><dd>%d</dd>" % data.get_total_loc())
        try:
            f.write(
                "<dt>Average file size</dt><dd>%.2f bytes</dd>"
                % (float(data.get_total_size()) / data.get_total_files())
            )
        except ZeroDivisionError:
            pass
        f.write("</dl>\n")

        # Files :: File count by date
        f.write(html_header(2, "File count by date"))

        # use set to get rid of duplicate/unnecessary entries
        files_by_date = set()
        for stamp in sorted(data.files_by_stamp.keys()):
            files_by_date.add(
                "%s %d"
                % (
                    datetime.datetime.fromtimestamp(stamp).strftime("%Y-%m-%d"),
                    data.files_by_stamp[stamp],
                )
            )

        fg = open(path + "/files_by_date.dat", "w")
        for line in sorted(list(files_by_date)):
            fg.write("%s\n" % line)
        # for stamp in sorted(data.files_by_stamp.keys()):
        # 	fg.write('%s %d\n' % (datetime.datetime.fromtimestamp(stamp).strftime('%Y-%m-%d'), data.files_by_stamp[stamp]))
        fg.close()

        f.write('<img src="files_by_date.png" alt="Files by Date">')

        # f.write('<h2>Average file size by date</h2>')

        # Files :: Extensions
        f.write(html_header(2, "Extensions"))
        f.write(
            '<table class="sortable" id="ext"><tr><th>Extension</th><th>Files (%)</th><th>Lines (%)</th><th>Lines/file</th></tr>'
        )

        for ext in sorted(data.extensions.keys()):
            files = data.extensions[ext]["files"]
            lines = data.extensions[ext]["lines"]
            try:
                loc_percentage = (100.0 * lines) / data.get_total_loc()
            except ZeroDivisionError:
                loc_percentage = 0
            f.write(
                "<tr><td>%s</td><td>%d (%.2f%%)</td><td>%d (%.2f%%)</td><td>%d</td></tr>"
                % (
                    ext,
                    files,
                    (100.0 * files) / data.get_total_files(),
                    lines,
                    loc_percentage,
                    lines / files,
                )
            )
        f.write("</table>")

        f.write("</body></html>")
        f.close()

    def create_lines_html(self, data, path):
        ###
        # Lines
        f = open(path + "/lines.html", "w")
        self.print_header(f)
        f.write("<h1>Lines</h1>")
        self.print_nav(f)

        f.write("<dl>\n")
        f.write("<dt>Total lines</dt><dd>%d</dd>" % data.get_total_loc())
        f.write("</dl>\n")

        f.write(html_header(2, "Lines of Code"))
        f.write('<img src="lines_of_code.png" alt="Lines of Code">')

        fg = open(path + "/lines_of_code.dat", "w")
        for stamp in sorted(data.changes_by_date.keys()):
            fg.write("%d %d\n" % (stamp, data.changes_by_date[stamp]["lines"]))
        fg.close()

        f.write("</body></html>")
        f.close()

    def create_tags_html(self, data, path):
        ###
        # tags.html
        f = open(path + "/tags.html", "w")
        self.print_header(f)
        f.write("<h1>Tags</h1>")
        self.print_nav(f)

        f.write("<dl>")
        f.write("<dt>Total tags</dt><dd>%d</dd>" % len(data.tags))
        if len(data.tags) > 0:
            f.write(
                "<dt>Average commits per tag</dt><dd>%.2f</dd>"
                % (1.0 * data.get_total_commits() / len(data.tags))
            )
        f.write("</dl>")

        f.write('<table class="tags">')
        f.write("<tr><th>Name</th><th>Date</th><th>Commits</th><th>Authors</th></tr>")
        # sort the tags by date desc
        tags_sorted_by_date_desc = [
            el[1]
            for el in reversed(
                sorted([(el[1]["date"], el[0]) for el in list(data.tags.items())])
            )
        ]
        for tag in tags_sorted_by_date_desc:
            authorinfo = []
            self.authors_by_commits = get_keys_sorted_by_values(
                data.tags[tag]["authors"]
            )
            for i in reversed(self.authors_by_commits):
                authorinfo.append("%s (%d)" % (i, data.tags[tag]["authors"][i]))
            f.write(
                "<tr><td>%s</td><td>%s</td><td>%d</td><td>%s</td></tr>"
                % (
                    tag,
                    data.tags[tag]["date"],
                    data.tags[tag]["commits"],
                    ", ".join(authorinfo),
                )
            )
        f.write("</table>")

        f.write("</body></html>")
        f.close()

    def create_graphs(self, path):
        print("Generating graphs...")
        self.create_graph_hour_of_day(path)
        self.create_graph_day_of_week(path)
        self.create_graph_domains(path)
        self.create_graph_month_of_year(path)
        self.create_graph_commits_by_year_month(path)
        self.create_graph_commits_by_year(path)
        self.create_graph_files_by_date(path)
        self.create_graph_lines_of_code(path)
        self.create_graph_lines_of_code_by_author(path)
        self.create_graph_commits_by_author(path)
        self.create_graph_by_gnuplot(path)

    def create_graph_hour_of_day(self, path):
        # hour of day
        f = open(path + "/hour_of_day.plot", "w")
        f.write(GNUPLOT_COMMON)
        f.write(
            """
set output 'hour_of_day.png'
unset key
set xrange [0.5:24.5]
set yrange [0:]
set xtics 4
set grid y
set ylabel "Commits"
plot 'hour_of_day.dat' using 1:2:(0.5) w boxes fs solid
"""
        )
        f.close()

    def create_graph_day_of_week(self, path):
        # day of week
        f = open(path + "/day_of_week.plot", "w")
        f.write(GNUPLOT_COMMON)
        f.write(
            """
set output 'day_of_week.png'
unset key
set xrange [0.5:7.5]
set yrange [0:]
set xtics 1
set grid y
set ylabel "Commits"
plot 'day_of_week.dat' using 1:3:(0.5):xtic(2) w boxes fs solid
"""
        )
        f.close()

    def create_graph_domains(self, path):
        # Domains
        f = open(path + "/domains.plot", "w")
        f.write(GNUPLOT_COMMON)
        f.write(
            """
set output 'domains.png'
unset key
unset xtics
set yrange [0:]
set grid y
set ylabel "Commits"
plot 'domains.dat' using 2:3:(0.5) with boxes fs solid, '' using 2:3:1 with labels rotate by 45 offset 0,1
"""
        )
        f.close()

    def create_graph_month_of_year(self, path):
        # Month of Year
        f = open(path + "/month_of_year.plot", "w")
        f.write(GNUPLOT_COMMON)
        f.write(
            """
set output 'month_of_year.png'
unset key
set xrange [0.5:12.5]
set yrange [0:]
set xtics 1
set grid y
set ylabel "Commits"
plot 'month_of_year.dat' using 1:2:(0.5) w boxes fs solid
"""
        )
        f.close()

    def create_graph_commits_by_year_month(self, path):
        # commits_by_year_month
        f = open(path + "/commits_by_year_month.plot", "w")
        f.write(GNUPLOT_COMMON)
        f.write(
            """
set output 'commits_by_year_month.png'
unset key
set yrange [0:]
set xdata time
set timefmt "%Y-%m"
set format x "%Y-%m"
set xtics rotate
set bmargin 5
set grid y
set ylabel "Commits"
plot 'commits_by_year_month.dat' using 1:2:(0.5) w boxes fs solid
"""
        )
        f.close()

    def create_graph_commits_by_year(self, path):
        # commits_by_year
        f = open(path + "/commits_by_year.plot", "w")
        f.write(GNUPLOT_COMMON)
        f.write(
            """
set output 'commits_by_year.png'
unset key
set yrange [0:]
set xtics 1 rotate
set grid y
set ylabel "Commits"
set yrange [0:]
plot 'commits_by_year.dat' using 1:2:(0.5) w boxes fs solid
"""
        )
        f.close()

    def create_graph_files_by_date(self, path):
        # Files by date
        f = open(path + "/files_by_date.plot", "w")
        f.write(GNUPLOT_COMMON)
        f.write(
            """
set output 'files_by_date.png'
unset key
set yrange [0:]
set xdata time
set timefmt "%Y-%m-%d"
set format x "%Y-%m-%d"
set grid y
set ylabel "Files"
set xtics rotate
set ytics autofreq
set bmargin 6
plot 'files_by_date.dat' using 1:2 w steps
"""
        )
        f.close()

    def create_graph_lines_of_code(self, path):
        # Lines of Code
        f = open(path + "/lines_of_code.plot", "w")
        f.write(GNUPLOT_COMMON)
        f.write(
            """
set output 'lines_of_code.png'
unset key
set yrange [0:]
set xdata time
set timefmt "%s"
set format x "%Y-%m-%d"
set grid y
set ylabel "Lines"
set xtics rotate
set bmargin 6
plot 'lines_of_code.dat' using 1:2 w lines
"""
        )
        f.close()

    def create_graph_lines_of_code_by_author(self, path):
        # Lines of Code Added per author
        f = open(path + "/lines_of_code_by_author.plot", "w")
        f.write(GNUPLOT_COMMON)
        f.write(
            """
set terminal png transparent size 640,480
set output 'lines_of_code_by_author.png'
set key left top
set yrange [0:]
set xdata time
set timefmt "%s"
set format x "%Y-%m-%d"
set grid y
set ylabel "Lines"
set xtics rotate
set bmargin 6
plot """
        )
        i = 1
        plots = []
        for a in self.authors_to_plot:
            i = i + 1
            author = a.replace('"', '\\"').replace("`", "")
            plots.append(
                """'lines_of_code_by_author.dat' using 1:%d title "%s" w lines"""
                % (i, author)
            )
        f.write(", ".join(plots))
        f.write("\n")

        f.close()

    def create_graph_commits_by_author(self, path):
        # Commits per author
        f = open(path + "/commits_by_author.plot", "w")
        f.write(GNUPLOT_COMMON)
        f.write(
            """
set terminal png transparent size 640,480
set output 'commits_by_author.png'
set key left top
set yrange [0:]
set xdata time
set timefmt "%s"
set format x "%Y-%m-%d"
set grid y
set ylabel "Commits"
set xtics rotate
set bmargin 6
plot """
        )
        i = 1
        plots = []
        for a in self.authors_to_plot:
            i = i + 1
            author = a.replace('"', '\\"').replace("`", "")
            plots.append(
                """'commits_by_author.dat' using 1:%d title "%s" w lines"""
                % (i, author)
            )
        f.write(", ".join(plots))
        f.write("\n")

        f.close()

    def create_graph_by_gnuplot(self, path):
        os.chdir(path)
        files = glob.glob(path + "/*.plot")
        for f in files:
            out = get_pipe_output([gnuplot_cmd + ' "%s"' % f])
            if len(out) > 0:
                print(out)

    def print_header(self, file) -> None:
        file.write(
            """<!DOCTYPE html>
<html>
<head>
	<meta charset="UTF-8">
	<title>GitStats - %s</title>
	<link rel="stylesheet" href="%s" type="text/css">
	<meta name="generator" content="GitStats %s">
	<script type="text/javascript" src="sortable.js"></script>
</head>
<body>
"""
            % (self.title, conf["style"], get_version)
        )

    def print_nav(self, file) -> None:
        """Print navigation menu to file."""
        file.write(
            """
            <div class="nav">
            <ul>
            <li><a href="index.html">General</a></li>
            <li><a href="activity.html">Activity</a></li>
            <li><a href="authors.html">Authors</a></li>
            <li><a href="files.html">Files</a></li>
            <li><a href="lines.html">Lines</a></li>
            <li><a href="tags.html">Tags</a></li>
            </ul>
            </div>
            """
        )


def html_header(level, text):
    name = html_linkify(text)
    return '\n<h%d id="%s"><a href="#%s">%s</a></h%d>\n\n' % (
        level,
        name,
        name,
        text,
        level,
    )


def html_linkify(text):
    return text.lower().replace(" ", "_")


def get_keys_sorted_by_values(dict):
    return [el[1] for el in sorted([(el[1], el[0]) for el in list(dict.items())])]


# dict['author'] = { 'commits': 512 } - ...key(dict, 'commits')
def get_keys_sorted_by_value_key(d, key):
    return [el[1] for el in sorted([(d[el][key], el) for el in list(d.keys())])]
