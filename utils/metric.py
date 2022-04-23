
def get_den(x, y):
    return x if x != 0 else y


def calc_error_ls(ref_ls, hyp_ls):
    assert type(ref_ls) == type(hyp_ls) == list
    assert len(ref_ls) == len(hyp_ls)
    return [(ref_ls[i] - hyp_ls[i]) / get_den(ref_ls[i], hyp_ls[i]) if hyp_ls[i] != 0 or ref_ls[i] != 0 else 0 for i in range(len(hyp_ls))]


def validate(ref: dict, hyp: dict):
    res = {}
    for key in hyp.keys():
        if key in ref.keys() and type(ref[key]) is list:
            if len(hyp[key]) != len(ref[key]):
                raise Exception(f"Variable list {key} has a different length in the reference!")
            error_ls = calc_error_ls(ref[key], hyp[key])
            mae = sum([abs(error_ls[i]) for i in range(len(error_ls))])/len(error_ls)
            _max = max(error_ls, key=abs)
            res[key] = (mae, _max, error_ls)
    return res


def retrieve_reference(model_name="sam_pv_standalone"):
    entries = {}

    with open( model_name, newline='') as file:
        lines = file.readlines()
        for line in lines:
            line = line.strip()
            if len(line) > 0 and line[0] != '#':
                # assignment
                if '=' in line:
                    var = line[0:line.index('=')].strip()
                    data = line[line.index('=')+1:].strip()
                    # parse list
                    if data[0] == '[' and data[-1] == ']':
                        data = data[1:-1].split(',')
                        data = [float(i.strip()) for i in data]
                        entries[var] = data
                    elif data[0] == '"' and data[-1] == '"':
                        data = data[1:-1]
                        entries[var] = data
    return entries


def _len(s, width=20):
    return width - len(str(s))


def algined(*args, width=20):
    s = ""
    for arg in args:
        s += arg + " "*_len(arg, width=width)
    return s


def print_errors(ref, hyp, width=20):

    if "p_balance" in ref.keys():
        ref["p_surplus"] = [i if i > 0.5 else 0 for i in ref["p_balance"]]
        ref["p_balance"] = [i if abs(i) > 0.5 else 0 for i in ref["p_balance"]]
    if "p_balance" in hyp.keys():
        hyp["p_surplus"] = [i if i > 0.5 else 0 for i in hyp["p_balance"]]
        hyp["p_balance"] = [i if abs(i) > 0.5 else 0 for i in hyp["p_balance"]]

        print("incl bal:", len([i for i in hyp["p_balance"] if abs(i) > 0.5 ]))
        print("incl sur:", len([i for i in ref["p_surplus"] if i > 0.5 or i == 0]))
        print("incl bal:", len([i for i in ref["p_balance"] if abs(i) > 0.5 ]))

    errs = validate(ref, hyp)
    print()
    if "name" in ref.keys():
        print(f"Validation for \"{ref['name']}\"")
    print(algined("Variable", "MAE", "MAX", "SUM (REF)", "SUM (HYP)", width=width))
    for key in errs:
        mae = f"{errs[key][0]*100:.5f}%"
        _max = f"{errs[key][1]*100:.5f}%"
        _sum = f"{sum(ref[key]):.2f}"
        _sum2 = f"{sum(hyp[key]):.2f}"
        print(algined(key, mae, _max, _sum, _sum2, width=width))
    print()
    return errs