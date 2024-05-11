def get_int(x):
    try:
        int(x)
        return True
    except ValueError:
        return False

def get_float(x):
    try:
        float(x)
        return True
    except ValueError:
        return False

def round_to_nearest_int(x):
    if x > 0:
        return int(x + 0.5)
    else:
        return int(x - 0.5)

def temperature_to_analog_val(x):
    a = -0.0013767593104192077
    b = 1.1437454694202085
    c = -325.6233372772532
    d = 32191.835380081127
    y = int(a * x**3 + b * x**2 + c * x + d)
    return y

def analog_val_to_temperature(x):
    a = -3.884e-18
    b = 1.662e-13
    c = -2.721e-09
    d = 2.13e-05
    e = -0.08965
    f = 307.5
    y = int(a * x**5 + b * x**4 + c * x**3 + d * x**2 + e * x + f)
    return y
