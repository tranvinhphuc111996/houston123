import datetime


def get_timestamp(x=None, with_microsecond=False):
    if x is None:
        x = datetime.datetime.now()
    if with_microsecond:
        return x.strftime('%Y%m%d-%H%M-%f')
    else:
        return x.strftime('%Y%m%d-%H%M')
