# Voros: Scraper/parser for MLB Pitch data

## About
Get pitch-by-pitch data from MLB's API in a friendly format.
Named after [DIPS](https://en.wikipedia.org/wiki/Defense_independent_pitching_statistics)-inventor [Voros McCracken](https://en.wikipedia.org/wiki/Voros_McCracken).

### Usage

    In [1]: from voros import Scraper

    In [2]: from datetime import date

    In [3]: import pandas as pd

    In [4]: s = Scraper()

    In [5]: df = pd.DataFrame(s.run(date(2008, 4, 1), date(2008, 4, 2)))

    In [6]: df.head()
    Out[6]:
    away_team      ax      ay       az  batter break_angle break_length break_y  \
    0       ari  16.894  29.125  -21.117  455759       -32.6          6.5    23.7
    1       ari   9.003  23.273  -24.415  455759       -16.6          7.9    23.8
    2       ari   9.655  22.735  -29.378  455759       -15.3          9.1    23.8
    3       ari  16.483  29.234  -24.125  455759       -29.3          6.6    23.7
    4       ari  18.276   28.46  -22.469  455759       -33.5          7.0    23.7

    cc              des ...  type_confidence      vx0       vy0     vz0       x  \
    0       Called Strike ...            2.000  -12.388  -128.615  -4.967  103.86
    1       Called Strike ...            2.000   -8.481  -115.609  -2.181   78.11
    2                Ball ...            2.000    -7.97  -117.315  -4.537   66.95
    3                Ball ...            2.000  -13.938  -128.972   1.812  122.75
    4     In play, run(s) ...            2.000  -12.679  -127.693  -4.988  107.30

        x0       y    y0     z0 zone
    0  3.448  151.10  50.0  5.971    8
    1   3.48  132.97  50.0  6.271    3
    2  3.619  171.83  50.0   6.17   14
    3  3.495   88.07  50.0  6.046   11
    4  3.357  149.38  50.0  6.048    4

    [5 rows x 49 columns]


`Scraper().run(start_date, end_date)` is the only thing you really need. The
method returns a [generator](https://wiki.python.org/moin/Generators)
that yields a `dict` for every pitch. Each `dict` contains all the per-pitch
data MLB provides, as well as per-inning data. If you look [here](http://gd2.mlb.com/components/game/mlb/year_2008/month_04/day_01/gid_2008_04_01_anamlb_minmlb_1/inning/inning_all.xml),
it combines the attributes of the `inning` and `atbat` elements with those
of each `pitch` element.

#### Notes
In the interest of convenience, errors get converted to warnings. Thus, if your
wifi cuts out midway through, you'll still get _something_ back.

In the interest of reducing the number of pointless HTTP requests made, I tried
to be reasonable about dates. Games played between April and November are scraped,
with a modulo-ish mechanism resulting in the first game in April immediately following
the last game of the last year's playoffs.

~~There's no per-game date info, unfortunately. The only date information is in the
URL, and I couldn't think of an elegant way to propagate that through the parsing
process. Maybe I will someday! Coincidentally, I'm also accepting PRs, hint hint.~~
(There are actually _two_ separate date fields in the data itself&mdash;`start_tfs_zulu`
and `tfs_zulu`. They're even already in UTC for you! Local game times could be
recreated with a library like [`pytz`](https://pypi.python.org/pypi/pytz?) and
a mapping between home teams and timezones, but that's Beyond The Scope Of This
Work.)

You can get A LOT OF DATA this way. The code uses generators wherever
reasonable to cut down on memory usage, but you'll still probably regret trying
to turn an entire season's worth of games into a single in-memory `DataFrame`,
so...don't? You can either throttle in the scraping, or use something like
[`itertools.islice`](https://docs.python.org/2/library/itertools.html#itertools.islice)
on the generator that gets returned, e.g.:

    lmt = 100
    idx = 0
    g = voros.Scraper().run(start, end)
    res = islice(g, lmt)
    while res:
        fname = 'pitch_data_{}.csv'.format(idx)
        # seems like overkill until you see your 9th error about
        # `csv.DictWriter` encountering an unfamiliar field
        pd.DataFrame(res).to_csv(fname)
        idx += 1
        res = islice(g, lmt)




## Credits
Inspired by [John Choiniere's `pfx_parser`](https://github.com/johnchoiniere/pfx_parser).
Written by [Sam Raker](https://swizzard.pizza).


