import calendar
from collections import Iterator
from copy import copy
import csv
from datetime import date
from functools import partial
from itertools import chain
import re
import warnings

from bs4 import BeautifulSoup
import requests


class Scraper(object):
    def __init__(self):
        self.start_url = 'http://gd2.mlb.com/components/game/mlb/'
        self.min_date = date(2008, 4, 1)
        self.max_date = date(date.today().year, 11, 1)
        self.today = date.today()
        self.gid_pat = re.compile(r'gid_\d{4}_\d{2}_\d{2}_*')

    def run(self, start_date=None, end_date=None):
        return self.parse(self.scrape(start_date, end_date))

    def scrape(self, start_date=None, end_date=None):
        start_date = start_date or self.min_date
        end_date = end_date or self.max_date
        curr_date = start_date
        while True:
            if curr_date > end_date:
                break
            days_to_scrape = self.days_to_scrape(curr_date.year, curr_date.month)
            for day_idx in xrange(*days_to_scrape):
                for game_url in self.get_day_games(curr_date.year,
                                                   curr_date.month, day_idx):
                    try:
                        req = requests.get(game_url)
                        req.raise_for_status()
                        yield self.to_soup(req)
                    except Exception as e:
                        warnings.warn(str(e))
            curr_date = self.inc_date(curr_date)

    def parse(self, game_or_games):
        if not isinstance(game_or_games, Iterator):
            game_or_games = [game_or_games]
        for game in game_or_games:
            for inning in game.find_all('inning'):
                for at_bat in self.parse_inning(inning):
                    for pitch in at_bat:
                        yield pitch

    def days_to_scrape(self, year, month):
        dow_first_day, last_day = calendar.monthrange(year, month)
        if year == self.max_date.year and month == self.max_date.month:
            last_day = self.max_day + 1
        else:
            last_day += 1
        return (6 - dow_first_day), last_day

    def fmt_url(self, year, month, day):
        return self.start_url + 'year_{}/month_{:02}/day_{:02}/'.format(
            year, month, day)

    def get_gids(self, soup):
        gids = soup.find_all(string=self.gid_pat)
        return [g.strip() for g in gids]

    def get_day_games(self, year, month, day):
        url = self.fmt_url(year, month, day)
        req = requests.get(url)
        gids = self.get_gids(self.to_soup(req))
        return ['{}{}{}'.format(url, gid, 'inning/inning_all.xml') for gid
                in self.get_gids(self.to_soup(req))]

    def parse_inning(self, inning_soup):
        return [self.parse_at_bat(at_bat, copy(inning_soup.attrs)) for at_bat
                in inning_soup.find_all('atbat')]

    def parse_at_bat(self, at_bat, ctx):
        ctx.update(event=at_bat.attrs['event'], batter=at_bat.attrs['batter'],
                   pitcher=at_bat.attrs['pitcher'])
        for pitch in at_bat.find_all('pitch'):
            yield {k: self._convert(v) for k, v in
                   chain(ctx.iteritems(), pitch.attrs.iteritems())}

    @staticmethod
    def to_soup(req):
        return BeautifulSoup(req.content, "lxml")

    @staticmethod
    def inc_date(d):
        if d.month < 11:
            return date(d.year, d.month + 1, 1)
        else:
            return date(d.year + 1, 4, 1)

    @staticmethod
    def _convert(v):
        if isinstance(v, basestring):
            return v.encode('ascii', 'xmlcharrefreplace')
        else:
            return v

