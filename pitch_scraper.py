import calendar
from datetime import date
from functools import partial
import re

from bs4 import BeautifulSoup
import requests



class PitchScraper(object):
    def __init__(self, starting_year=2008):
        self.start_url = 'http://gd2.mlb.com/components/game/mlb/'
        self.start_month = 4
        self.start_year = starting_year
        today = date.today()
        self.max_year = today.year
        self.max_month = today.month
        self.max_day = today.day
        self.gid_pat = re.compile(r'gid_\d{4}_\d{2}_\d{2}_*')

    @staticmethod
    def to_soup(req):
        return BeautifulSoup(req.content, "lxml")

    def days_to_scrape(self, year, month):
        dow_first_day, last_day = calendar.monthrange(year, month)
        if year == self.max_year and month == self.max_month:
            last_day = self.max_day
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

    def scrape(self, end_month=None, end_year=None):
        end_month = end_month or self.max_month
        end_year = end_year or self.max_year
        if end_month < self.start_month:
            raise ValueError("End month must be greater than start month")
        if end_year < self.start_year:
            raise ValueError("End year must be greater than start year")
        curr_month = self.start_month
        curr_year = self.start_year
        while True:
            if end_month is not None and curr_month > end_month:
                break
            if end_year is not None and curr_year > end_year:
                break
            days_to_scrape = self.days_to_scrape(curr_year, curr_month)
            for day_idx in xrange(*days_to_scrape):
                for game_url in self.get_day_games(curr_year, curr_month, day_idx):
                    req = requests.get(game_url)
                    yield self.to_soup(req)
            curr_month += 1
            curr_year += 1

