"""Function that calls eval for calculator.

It is separated into a module in order to import * from numpy and thus
simplify writing expressions. (Such import is not allowed inside a
function.)

"""

from numpy import *


def evaluate(statements, expression, globals_dict):
    """Evaluate expression and return results."""
    exec(statements)
    globals_dict.update(globals())
    globals_dict.update(locals())
    return eval(expression, globals_dict)
