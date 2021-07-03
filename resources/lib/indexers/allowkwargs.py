from inspect import getargspec
from functools import wraps


def allow_kwargs(foo):
    argspec = getargspec(foo)
    # if the original allows kwargs then do nothing
    if argspec.keywords:
        return foo

    @wraps(foo)
    def newfoo(*args, **kwargs):
        #print "newfoo called with args=%r kwargs=%r"%(args,kwargs)
        some_args = dict((k, kwargs[k]) for k in argspec.args if k in kwargs)
        return foo(*args, **some_args)

    return newfoo
