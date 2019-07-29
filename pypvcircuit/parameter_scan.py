from itertools import product
from functools import partial, reduce
import operator
import numpy as np
import pandas as pd


def testfunc(a, b):
    return a + b


def testfunc2(a, b, c):
    return a, b + c


test_param = [{'a': [1, 2], 'b': [3, 4]}]

test_param2 = [{'a': [1, 2], 'b': [2, 3], 'c': [1]}]


def yield_param(param_grid):
    for p in param_grid:
        # Always sort the keys of a dictionary, for reproducibility
        items = sorted(p.items())
        if not items:
            yield {}
        else:
            keys, values = zip(*items)
            for v in product(*values):
                params = dict(zip(keys, v))
                yield params


def count_len(param_grid):
    product = partial(reduce, operator.mul)
    return sum(product(len(v) for v in p.values()) if p else 1
               for p in param_grid)


def run_search(func, param_grid):
    for params in yield_param(param_grid):
        c = func(**params)
        print(c)


def run_search_to_numpy(func, param_grid):
    param_grid_len = count_len(param_grid)
    print("total counts: {}".format(param_grid_len))

    # construct a 2-D array
    param_names = None

    param_array = np.empty((param_grid_len, len(param_grid[0])))
    index = 0

    result_array = []
    for params in yield_param(param_grid):
        if param_names is None:
            param_names = [col for col in params.keys()]

        for jj, pp in enumerate(params.keys()):
            param_array[index, jj] = params[pp]
        index += 1
        c = func(**params)
        result_array.append(c)

    return param_names, param_array, result_array


if __name__ == "__main__":
    run_search(testfunc, test_param)
    _, p, a = run_search_to_numpy(testfunc2, test_param2)
    print(p, a)
    print(np.array(a))
