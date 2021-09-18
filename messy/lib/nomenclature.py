

import json

__locations__ = None


def load_location_data(infile):
    global __locations__
    __locations__ = json.load(open(infile))
    return __locations__


def get_location_abbr(location):
    tokens = list(x.strip() for x in location.split('/'))
    if len(tokens) >= 3:
        return __locations__[tokens[0]][tokens[1]][tokens[2]], tokens[1]
    return '', ''


def create_name(species, host, location, acc_code, collection_date):
    if species == 'betacoronavirus-ncov19':
        if host == 'human':
            prefix = 'hCov19'
    else:
        return ''

    abbr, country = get_location_abbr(location)
    if not (abbr and country):
        return ''

    return f'{prefix}/{country}/{abbr}-{acc_code}/{collection_date.year}'
