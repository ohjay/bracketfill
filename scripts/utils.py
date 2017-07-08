#!/Library/Frameworks/Python.framework/Versions/2.7/bin/python

import sys
import time

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
