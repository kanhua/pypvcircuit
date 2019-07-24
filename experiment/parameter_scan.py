from itertools import product


def testfunc(a, b):
    return a + b


test_param = [{'a': [1, 2], 'b': [3, 4]}]


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


def run_search(func, param_grid):
    for params in yield_param(param_grid):
        c = func(**params)
        print(c)


if __name__ == "__main__":
    run_search(testfunc, test_param)
