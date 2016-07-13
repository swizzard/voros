import csv
from functools import partial
from itertools import chain
import warnings


class PitchParser(object):
    def __init__(self, wanted_attrs=None):
        default_wanted = ['batter_id', 'pitcher_id', 'des', 'pitch_type',
                          'type', 'pitch_idx', 'des', 'event', 'is_hit',
                          'balls', 'strikes']
        self.wanted_attrs = wanted_attrs or default_wanted

    def new_dict(self, **kwargs):
        d = dict.fromkeys(self.wanted_attrs)
        d.update(**kwargs)
        return d

    def parse_inning(self, inning_soup):
        ctx = {'inning_num': inning_soup.attrs['num']}
        return [self.parse_at_bat(at_bat, inning_soup.attrs['num']) for at_bat
                in inning_soup.find_all('atbat')]


    def parse_at_bat(self, at_bat, inning_num):
        event = at_bat.attrs['event']
        batter_id = at_bat.attrs['batter']
        pitcher_id = at_bat.attrs['pitcher']
        pitches = []
        balls = 0
        strikes = 0
        for idx, pitch in enumerate(at_bat.find_all('pitch')):
            dct = self.new_dict(event=event, batter_id=batter_id,
                                pitcher_id=pitcher_id, pitch_idx=idx,
                                inning_num=inning_num)
            for key in dct:
                if key in pitch.attrs:
                    dct[key] = pitch.attrs[key]
            if dct['type'] == 'S':
                strikes += 1
            elif dct['type'] == 'B':
                balls += 1
            dct['balls'] = balls
            dct['strikes'] = strikes
            dct['is_hit'] = 'In play' in dct['des']
            pitches.append(dct)
        return pitches

    def parse_game(self, soup):
        for inning in soup.find_all('inning'):
            for at_bat in self.parse_inning(inning):
                for pitch in at_bat:
                    yield pitch


class PitchWriter(object):
    def __init__(self, attrs, outfile=None, **csv_kwargs):
        self.writer = partial(csv.DictWriter, fieldnames=attrs, **csv_kwargs)
        self.outfile = outfile

    def write(self, pitches, outfile=None):
        outfile = outfile or self.outfile
        if outfile is None:
            import sys
            # http://stackoverflow.com/questions/2374427/python-2-x-write-binary-output-to-stdout
            if sys.platform == 'win32':
                import os, msvcrt
                msvcrt.setmode(sys.stdout.fileno(), os.O_BINARY)
            outfile = sys.stdout
            needs_closing = False
        else:
            outfile = open(outfile, 'wb')
            needs_closing = True
        try:
            writer = self.writer(outfile)
            writer.writeheader()
            for pitch in pitches:
                writer.writerow(pitch)
        except Exception:
            raise
        finally:
            if needs_closing:
                outfile.close()

