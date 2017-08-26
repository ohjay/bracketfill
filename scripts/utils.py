#!/Library/Frameworks/Python.framework/Versions/2.7/bin/python

import sys
import time
import os, shutil

outstanding_tasks = []

def verbose(task):
    def _decorated(fn):
        def _fn(*args, **kwargs):
            outstanding_tasks.append(task)
            indent = '  ' * (len(outstanding_tasks) - 1)
            print('%s[o] %s is in progress.' % (indent, task))
            start_time = time.time()
            result = fn(*args, **kwargs)
            print('%s[o] %s has finished (%.2fs elapsed).\n' % (indent, task, time.time() - start_time))
            del outstanding_tasks[-1]
            return result
        return _fn
    return _decorated

def print_memory_usage(lst, prefix=''):
    print('%sMemory usage: %.3f MB' % (prefix, float(sys.getsizeof(lst)) / 1e6))

def rm_rf(dir, require_confirmation=True):
    print('WARNING: about to delete the full contents of `%s`!' % dir)
    if require_confirmation:
        confirmation = raw_input('Are you sure you want to proceed? (True/False) ')
    else:
        confirmation = True
    if (isinstance(confirmation, bool) and confirmation) \
            or (isinstance(confirmation, str) and confirmation.lower() == 'true'):
        for filename in os.listdir(dir):
            filepath = os.path.join(dir, filename)
            try:
                if os.path.isfile(filepath):
                    os.unlink(filepath)
                elif os.path.isdir(filepath):
                    shutil.rmtree(filepath)
            except Exception as e:
                print(e)
        print('Successfully removed everything inside of `%s`.' % dir)
        return True
    else:
        print('Operation `rm -rf %s` aborted.' % dir)
        return False
