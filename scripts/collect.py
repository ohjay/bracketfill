#!/Library/Frameworks/Python.framework/Versions/2.7/bin/python

import re
import os
import utils
import json
import requests
import cPickle

API_BASE_DEFAULT = 'https://api.smash.gg'
EVENT_DEFAULT = 'melee-singles'
MEM_DISPLAY_FREQ = 20

def get_bracket_data(api_base, id, entrants, date):
    url = '%s/phase_group/%s?expand[]=sets&expand[]=seeds' % (api_base, id)
    response = json.loads(requests.get(url).content)
    if not response.get('success', True) or 'entities' not in response:
        return []  # could raise an error, but let's go with this for now

    for _seed in response['entities'].get('seeds', ()):
        try:
            eid = int(_seed['mutations']['entrants'].keys()[0])
        except ValueError:
            continue
        pid, info = _seed['mutations']['players'].items()[0]
        entrants[eid] = {
            'gamerTag': info['gamerTag'],
            'country': info['country'],
            'state': info['state'],
            'prefix': info['prefix'],
        }

    __data = []
    for _set in response['entities'].get('sets', ()):
        entrant1 = entrants.get(_set['entrant1Id'], None)
        entrant2 = entrants.get(_set['entrant2Id'], None)
        if entrant1 is None or entrant2 is None:
            continue

        entrant1_score = _set['entrant1Score']
        entrant2_score = _set['entrant2Score']
        if entrant1_score is None or entrant2_score is None:
            continue

        winner = 1 if entrant1_score > entrant2_score else 2
        is_gf = _set['isGF']
        best_of = max(entrant1_score, entrant2_score) * 2 - 1

        __data.append({
            'entrant1': entrant1,
            'entrant2': entrant2,
            'entrant1_score': entrant1_score,
            'entrant2_score': entrant2_score,
            'winner': winner,
            'is_gf': is_gf,
            'best_of': best_of,
            'date': date,
        })
    return __data

def get_tournament_data(api_base, tournament, event):
    url = '%s/tournament/%s/event/%s?expand[]=groups' % (api_base, tournament, event)
    response = json.loads(requests.get(url).content)
    if not response.get('success', True) or 'entities' not in response:
        raise ValueError('tournament "{0}" does not exist, or event "{1}" does not exist at "{0}"'.format(tournament, event))

    event_entity = response['entities'].get('event', None)
    if event_entity is None:
        raise ValueError('tournament %s has no date attached' % tournament)

    tournament_date = event_entity['startAt']
    entrants, _data = {}, []
    for _group in response['entities'].get('groups', ()):  # by Smash.gg terminology, a group is a bracket
        date = _group.get('startAt', tournament_date)
        if not date or int(date) < 0:
            date = tournament_date
        _data.extend(get_bracket_data(api_base, _group['id'], entrants, date))
    return _data

def get_slugs(url_path):
    with open(url_path, 'r') as urlfile:
        slugs = set(','.join(urlfile.readlines()).split(','))
        slugs = map(lambda u: re.match(r'^https://smash.gg/tournament/([^\s^/]+)$', u), slugs)
        slugs = map(lambda m: m.group(1), filter(None, slugs))
    return slugs

@utils.verbose('Smash.gg querying')
def collect_smash_gg(sgg_config, root):
    assert 'tournament_url_file' in sgg_config, 'a URL file must be specified for Smash.gg collection'
    url_path = os.path.join(root, sgg_config['tournament_url_file'])
    api_base = sgg_config.get('api-base', API_BASE_DEFAULT)
    event = sgg_config.get('event', EVENT_DEFAULT)

    data = []
    for i, tournament in enumerate(get_slugs(url_path)):
        try:
            data.extend(get_tournament_data(api_base, tournament, event))
            if i % MEM_DISPLAY_FREQ == 0:
                prefix = '[%s] ' % str(i).zfill(4)
                utils.print_memory_usage(data, prefix=prefix)
        except ValueError as e:
            print('[-] %s' % str(e))
            continue  # nonexistent tournament/event

    outfile = sgg_config['tournament_url_file'].replace('urls_', '').replace('urls', '')
    if '.' in outfile:
        outfile = outfile[:outfile.rfind('.')]
    outfile = os.path.join(root, outfile + '.pickle')
    with open(outfile, 'wb') as handle:
        cPickle.dump(data, handle, protocol=cPickle.HIGHEST_PROTOCOL)

@utils.verbose('Initial debugging')
def run_debug_initial():
    return True

def collect(config, debug=False):
    if debug and not run_debug_initial():
        return  # `run_debug_initial` should return True if the program is meant to continue afterward

    data_params = config['data']
    root = data_params.get('root', '')

    collect_config = data_params.get('collect', None)
    if not collect_config:
        print('[o] No data collection to be done.')
    elif 'smash_gg' in collect_config:
        collect_smash_gg(collect_config['smash_gg'], root)
