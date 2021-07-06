# from https://www.programcreek.com/python/example/712/difflib.unified_diff

import difflib
import json
import optparse
import os
import sys
import time
import webbrowser
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent


def main():
    usage = "usage: %prog [options] fromfile tofile"
    parser = optparse.OptionParser(usage)
    parser.add_option("-c", action="store_true", default=False, help='Produce a context format diff (default)')
    parser.add_option("-u", action="store_true", default=False, help='Produce a unified format diff')
    parser.add_option("-m", action="store_true", default=False,
                      help='Produce HTML side by side diff (can use -c and -l in conjunction)')
    parser.add_option("-n", action="store_true", default=False, help='Produce a ndiff format diff')
    parser.add_option("-l", "--lines", type="int", default=3, help='Set number of context lines (default 3)')
    (options, args) = parser.parse_args()

    if len(args) == 0:
        parser.print_help()
        sys.exit(1)
    if len(args) != 2:
        parser.error("need to specify both a fromfile and tofile")

    n = options.lines
    fromfile, tofile = args

    fromdate = time.ctime(os.stat(fromfile).st_mtime)
    todate = time.ctime(os.stat(tofile).st_mtime)
    fromlines = json.dumps(json.load(open(fromfile, 'U')), indent=2).splitlines()
    tolines = json.dumps(json.load(open(tofile, 'U')), indent=2).splitlines()

    if options.u:
        diff = difflib.unified_diff(fromlines, tolines, fromfile, tofile, fromdate, todate, n=n)
    elif options.n:
        diff = difflib.ndiff(fromlines, tolines)
    elif options.m:
        diff = difflib.HtmlDiff().make_file(fromlines, tolines, fromfile, tofile, context=options.c, numlines=n)
    else:
        diff = difflib.context_diff(fromlines, tolines, fromfile, tofile, fromdate, todate, n=n)

    output = f'{BASE_DIR}/json_diff_output.html'
    with open(output, 'w') as f:
        f.writelines(diff)
    webbrowser.open('file://' + output)


if __name__ == '__main__':
    main()
