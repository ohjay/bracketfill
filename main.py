#!/Library/Frameworks/Python.framework/Versions/2.7/bin/python

import os
import yaml
import argparse

from scripts.collect import collect
from scripts.parse import parse
from scripts.train import train
from scripts.evaluate import evaluate

ROOT = '/Users/owenjow/bracketfill'

def error(*args, **kwargs):
    print('[-] Error: command not recognized')

def handler(command):
    return {
        'collect': collect,
        'parse': parse,
        'train': train,
        'evaluate': evaluate,
    }.get(command, error)

def main(args):
    config = None
    if args.config:
        if not os.path.isfile(args.config):
            args.config = os.path.join(ROOT, args.config)
        assert os.path.isfile(args.config)
        config = yaml.load(open(args.config, 'r'))
    handler(args.command)(config, debug=args.debug)

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('command', choices=['collect', 'parse', 'train', 'evaluate'], default='train')
    parser.add_argument('--config', '-c', type=str, help='config file')
    parser.add_argument('--debug', '-d', action='store_true')
    args = parser.parse_args()

    main(args)
