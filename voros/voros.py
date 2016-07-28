"""
Scrape and parse data from the MLB Pitches API
"""
import calendar
from collections import Iterator
from copy import copy
from datetime import date
from itertools import chain
import re
import warnings

from bs4 import BeautifulSoup
import requests


class Scraper(object):
    """
    Scrape and parse data from the MLB Pitches API
    """
    def __init__(self):
        self.start_url = 'http://gd2.mlb.com/components/game/mlb/'
        self.min_date = date(2008, 4, 1)
        self.max_date = date(date.today().year, 11, 1)
        self.today = date.today()
        self.gid_pat = re.compile(r'gid_\d{4}_\d{2}_\d{2}_*')

    def run(self, start_date=None, end_date=None):
        """
        Scrape and parse data
        :param start_date: earliest date to scrape
        :param end_date: latest date to scrape
        :type start_date, end_date: datetime.date object
        :return: generator of dicts
        """
        return self.parse(self.scrape(start_date, end_date))

    def scrape(self, start_date=None, end_date=None):
        """
        Scrape XML pages from the API and convert it to `BeautifulSoup` objects
        :param start_date: earliest date to scrape
        :param end_date: latest date to scrape
        :type start_date, end_date: datetime.date object
        :return: generator of BeautifulSoup objects
        """
        start_date = start_date or self.min_date
        end_date = end_date or self.max_date
        curr_date = start_date
        while True:
            for day in self.days_to_scrape(curr_date):
                if day > end_date:
                    break
                else:
                    for game_url in self.get_day_games(day):
                        try:
                            req = requests.get(game_url)
                            req.raise_for_status()
                            yield self.to_soup(req)
                        except Exception as e:
                            warnings.warn(str(e))
            else:
                curr_date = self.inc_date(curr_date)
                continue
            break

    def parse(self, game_or_games):
        """
        Extract data from games
        :param game_or_games: game(s) to parse
        :type game_or_games: iterator of BeautifulSoup objects, or a single
                             BeautifulSoup object
        :return: generator of dicts
        """
        if not isinstance(game_or_games, Iterator):
            game_or_games = [game_or_games]
        for game in game_or_games:
            for inning in game.find_all('inning'):
                for at_bat in self.parse_inning(inning):
                    for pitch in at_bat:
                        yield pitch

    def days_to_scrape(self, d):
        """
        Calculate range of days when games were played
        :param d: starting date to calculate month for
        :param year: year
        :param month: month
        :type year, month: int
        :return list of date
        """
        first_dow, last_day = calendar.monthrange(d.year, d.month)
        if d.month == 4:
            first = (6 - first_dow) or 1
        else:
            first = d.day
        last = min(date(d.year, d.month, last_day), self.max_date).day
        for day in xrange(first, last + 1):
            new_d = date(d.year, d.month, day)
            yield new_d

    def fmt_url(self, year, month, day):
        """
        Create a valid API URL
        :param year: year
        :param month: month
        :param day: day
        :type year, month, day: int
        :return: str
        """
        return self.start_url + 'year_{}/month_{:02}/day_{:02}/'.format(
            year, month, day)

    def get_gids(self, soup):
        """
        Extract links to games
        :param soup: the soup to parse
        :type soup: BeautifulSoup object
        :return: list of str
        """
        gids = soup.find_all(string=self.gid_pat)
        return [g.strip() for g in gids]

    def get_day_games(self, d):
        """
        Construct urls to games
        :param d: date
        :type d: datetime.date object
        :return: list of str
        """
        url = self.fmt_url(d.year, d.month, d.day)
        req = requests.get(url)
        for gid in self.get_gids(self.to_soup(req)):
            yield '{}{}{}'.format(url, gid, 'inning/inning_all.xml')

    def parse_inning(self, inning_soup):
        """
        Extract and parse at bats in an inning
        :param inning_soup: soup fragment representing an inning
        :type inning_soup: BeautifulSoup object
        :return: generator of generators of dicts
        """
        return (self.parse_at_bat(at_bat, copy(inning_soup.attrs)) for at_bat
                in inning_soup.find_all('atbat'))

    def parse_at_bat(self, at_bat, ctx):
        """
        Parse an at bat into dicts
        :param at_bat: soup fragment representing an at bat
        :type at_bat: BeautifulSoup object
        :param ctx: context info extracted from containing inning
        :type ctx: dict
        :yield: dict
        """
        ctx.update(at_bat.attrs)
        for pitch in at_bat.find_all('pitch'):
            yield {k: self._convert(v) for k, v in
                   chain(ctx.iteritems(), pitch.attrs.iteritems())}

    @staticmethod
    def to_soup(resp):
        """
        Convert a response's content into a BeautifulSoup object
        :param resp: response to convert
        :type resp: requests.models.Response
        :return: BeautifulSoup object
        """
        return BeautifulSoup(resp.content, "xml")

    @staticmethod
    def inc_date(d):
        """
        Increment a date by one month, 'rolling over' to the start of the
        following year's season if necessary
        :param d: date to increment
        :type d: datetime.date object
        :return: datetime.date object
        """
        if d.month < 11:
            return date(d.year, d.month + 1, 1)
        else:
            return date(d.year + 1, 4, 1)

    @staticmethod
    def _convert(v):
        """
        Ensure strings are representable in ASCII
        :param v: value
        :type v: any
        :return: value of the same type as v
        """
        if isinstance(v, basestring):
            return v.encode('ascii', 'xmlcharrefreplace')
        else:
            return v

