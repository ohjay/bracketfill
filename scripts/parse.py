#!/Library/Frameworks/Python.framework/Versions/2.7/bin/python

import os
import re
import csv
import utils
from fuzzywuzzy import fuzz

"""
parse.py
Files in the data folder -> Post-processed data in memory
"""

SETTINGS = {
    'fuzz_threshold': 70,
    'effective_inf': 1e10,
}

def character_index(character):
    """Transforms a SSBM character into an integer."""
    mapping = dict(enumerate(
        ['fox', 'falco', 'marth', 'sheik', 'jigglypuff', 'peach', 'ice climbers', 'falcon', 'pikachu',
         'samus', 'dr. mario', 'yoshi', 'luigi', 'ganondorf', 'mario', 'young link', 'donkey kong',
         'link', 'mr. game and watch', 'roy', 'mewtwo', 'zelda', 'ness', 'pichu', 'bowser', 'kirby', '']
    ))
    mapping = {v: k for k, v in mapping.iteritems()}
    return mapping[character.lower()]

@utils.verbose('H2H spreadsheet parsing')
def parse_h2h_spreadsheet(csv_path, csv_config):
    """Original application: `data/summer_2017.csv`
    :return: a nested dictionary of the form {tag: {opponent: [wins, losses]}}
    """
    limits = csv_config.get('limits', {'min_col': 0, 'max_col': SETTINGS['effective_inf']})
    if limits['max_col'] == -1:
        limits['max_col'] = SETTINGS['effective_inf']

    h2h_data = {}
    with open(csv_path, 'rb') as csvfile:
        reader = csv.reader(csvfile)
        tags = next(reader)[limits['min_col']:limits['max_col']+1]
        for tag, row in zip(tags, reader):
            h2h_data[tag] = {}
            row = row[limits['min_col']:limits['max_col']+1]
            for opponent, record in zip(tags, row):
                match = re.match(r'^([0-9]+)-([0-9]+)$', record)
                if match:
                    h2h_data[tag][opponent] = map(int, (match.group(1), match.group(2)))
    return h2h_data

def parse_profile_spreadsheet(csv_path):
    profiles = {}
    with open(csv_path, 'rb') as csvfile:
        reader = csv.reader(csvfile)
        attrs = ['_'.join(attr.lower().split()) for attr in next(reader) if len(attr) > 0]
        for row in reader:
            row[2] = character_index(row[2])  # main
            row[3] = character_index(row[3])  # secondary
            tag, row = row[1].lower(), row[:1] + row[2:]
            for i in range(len(row)):
                if row[i] == '':
                    row[i] = 5  # TODO: also have option to set to average / specify column defaults
            profiles[tag] = {attr: float(value) for attr, value in zip(attrs, row)}
    return profiles

def parse_sets(config):
    """Parse set information from SETS_SOURCE."""
    sets = []
    for source in config['train']['sets_source']:
        source = os.path.join(config['data']['root'], source)
        if source.endswith('csv'):
            # SOURCE assumed to consist of H2H spreadsheet data
            h2h_data = parse_h2h_spreadsheet(source, config['data']['csv_stats'])
            processed_tags = set()
            for tag0, records in h2h_data.items():
                for tag1, h2h in records.items():
                    if tag1 not in processed_tags:
                        # Add wins
                        for _ in range(h2h[0]):
                            sets.append({'tag0': tag0.lower(), 'tag1': tag1.lower(), 'winner': 0})
                        # Add losses
                        for _ in range(h2h[1]):
                            sets.append({'tag0': tag0.lower(), 'tag1': tag1.lower(), 'winner': 1})
                processed_tags.add(tag0)
        else:
            print('[-] ERROR: Unrecognized source: %s.' % source)
    return sets

def parse_players(config):
    """Parse player information from PLAYERS_SOURCE."""
    players = {}
    for source in config['train']['players_source']:
        source = os.path.join(config['data']['root'], source)
        if source.endswith('profiles.csv'):
            # SOURCE assumed to consist of general spreadsheet data
            profiles = parse_profile_spreadsheet(source)
            for tag in profiles:
                if tag not in players:
                    players[tag] = {}
                players[tag].update(profiles[tag])
        elif source.endswith('rankings.txt'):
            # SOURCE assumed to consist of a list of rankings
            with open(source) as f:
                curr_ranking = 0
                for line in f.readlines():
                    tag = line.strip().split()[-1]
                    if tag not in players:
                        players[tag] = {}
                    players[tag]['ranking'] = curr_ranking
                    curr_ranking += 1
        else:
            print('[-] ERROR: Unrecognized source: %s.' % source)
    return players

@utils.verbose('Initial debugging')
def run_debug_initial(*args, **kwargs):
    return True

def parse(config, debug=False):
    if debug and not run_debug_initial(config=config):
        return  # `run_debug_initial` should return True if the program is meant to continue afterward

    data_params = config['data']
    root = data_params.get('root', '')

    if 'tag' in data_params and 'fuzz_threshold' in data_params['tag']:
        SETTINGS['fuzz_threshold'] = data_params['tag']['fuzz_threshold']

    parsed = {}
    if 'csv_stats' in data_params:
        csv_config = data_params['csv_stats']
        csv_path = os.path.join(root, csv_config['path'])
        csv_type = csv_config['type']
        if csv_type == 'h2h':
            parsed['h2h'] = parse_h2h_spreadsheet(csv_path, csv_config)
        else:
            print('[-] CSV type not recognized')
