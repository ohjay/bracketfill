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

@utils.verbose('Set parsing')
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

@utils.verbose('Player parsing')
def parse_players(config):
    """Parse player information from PLAYERS_SOURCE."""
    players = {}
    for source in config['train']['players_source']:
        source = os.path.join(config['data']['root'], source)
        if source.endswith('player_profiles.csv'):
            # SOURCE assumed to consist of general spreadsheet data
            'TODO'
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
