#!/Library/Frameworks/Python.framework/Versions/2.7/bin/python

import os
import re
import csv
import utils
from fuzzywuzzy import fuzz

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

def parse_sets(sets_source):
    """Parse set information from SETS_SOURCE."""
    if sets_source.endswith('csv'):
        # SETS_SOURCE assumed to consist of H2H spreadsheet data
        return {}  # TODO
    else:
        print('[-] Unrecognized sets source: %s.' % sets_source)

def parse_players(players_source):
    """Parse player information from PLAYERS_SOURCE."""
    if players_source.endswith('csv'):
        # PLAYERS_SOURCE assumed to consist of filled spreadsheet data
        return {}  # TODO
    else:
        print('[-] Unrecognized players source: %s.' % players_source)

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
