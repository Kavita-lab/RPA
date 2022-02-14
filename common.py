import matplotlib.colors as mcolors
import math
import datetime


def shortner(given_color: str):
    given_color = given_color.lower()
    colors = list(mcolors.cnames.keys())
    for color in colors:
        if color in given_color:
            rfs = given_color.split(color)
            sc = color[:2] + color[-1]
            rl = rfs[0] + sc + rfs[1]
            if rl is None:
                return given_color
            else:
                return rl


def truncate(number, digits) -> float:
    stepper = 10.0 ** digits
    return math.trunc(stepper * number) / stepper


def get_name(file_name):
    current_datetime_stamp = (str(datetime.datetime.now()).split('.'))[0].replace(':', '-').replace(' ', '_')
    name = f'{file_name}_sku_output_{current_datetime_stamp}'
    return name
