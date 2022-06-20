"""Utility functions for managing and parsing park names."""

from hydra.utils import to_absolute_path

from .io import read_config_file


# It ends up being more efficient to keep these objects in memory rather than
# read them each time their contents are required
_PARK_NAMES = read_config_file(
    to_absolute_path('config/refresh_source_capta/all_parks.yaml')
)
_PARK_TYPES = read_config_file(
    to_absolute_path('config/refresh_source_capta/park_types.yaml')
)


def get_park_type(nps_park_name):
    """Extracts the (abbreviated) park type(s) (e.g., "NP", or "NM & NPRES")
    from a name contained in the park lists maintained in the configuration
    files. If a park matches more than one type then both types will be
    returned, separated by an ampersand.

    Args:
        nps_park_name (str): the NPS name for a park (e.g., "Acadia NP")

    Returns:
        str: the abbreviated park type(s)
    """
    park_types = []
    for w in nps_park_name.split(' '):
        if w in _PARK_TYPES:
            park_types.append(w)
        # Some park types are occasionally missing their initial "N" in the
        # lists, namely if they are the second of a pair of park types (e.g.,
        # "NM & PRES" rather than "NM & NPRES")
        elif 'N' + w in _PARK_TYPES:
            park_types.append('N' + w)
        # Some parks are listed as "Park" or "Parks," distinct from "NP"
        elif w in ['Park', 'Parks']:
            park_types.append('PK')
        # Certain memorials are just called "Memorial," distinct from "NMEM"
        elif w == 'Memorial':
            park_types.append('MEM')
    # There are four sporadic cases: the White House, the Washington
    # Monument, the National Visitor Center, and the JFK Center for the
    # Performing Arts, for which an empty string will be returned
    if not len(park_types):
        park_types.append('SPORADIC')

    return ' & '.join(park_types)


def get_full_park_name(park_code):
    """Returns a human-legible full name for a park (e.g., "Acadia
    National Park").

    Args:
        park_code (str): an abbreviated park name (e.g., "ACAD")

    Returns:
        str: the park's full name

    Raises:
        KeyError: if the park code is not recognized
    """
    nps_park_name = _PARK_NAMES.get(park_code)
    if nps_park_name is None:
        raise KeyError(f'Unrecognized park code {park_code}')
    park_type = get_park_type(nps_park_name)

    # Normally the park type will be present verbatim in the NPS name
    if park_type in nps_park_name:
        long_park_type = ' '.join([
            _PARK_TYPES.get(pt, '&')
            for pt in park_type.split(' ')
            if pt != ''
        ])
        full_park_name = nps_park_name.replace(park_type, long_park_type)
    # This may not be the case under three conditions: the park type is one of
    # the "synthetic" types "PK" or "MEM", the park is one of the four sporadic
    # parks (see above for a list), or an initial "N" has been added to a park
    # type in the NPS name
    else:
        # In the first two cases, no replacement is necessary to retrieve the
        # full name (in fact, these "synthetic" types need to exist to
        # streamline functionality in this codebase precisely because the
        # original names have none of the normal abbreviations)
        if park_type in ['MEM', 'PK', 'SPORADIC']:
            full_park_name = nps_park_name
        # In the third case, we need to remove the initial "N" from the second
        # type and adjust the replacement name accordingly
        else:
            long_park_type = 'National ' + ' '.join([
                _PARK_TYPES.get(pt, '&')
                for pt in park_type.split(' ')
                if pt != ''
            ]).replace('National ', '')
            split_type = park_type.split(' ')
            park_type = ' '.join(split_type[:-1] + [split_type[-1][1:]])
            full_park_name = nps_park_name.replace(park_type, long_park_type)

    return full_park_name


def get_long_park_type(park_type_code):
    """Returns the unabbreviated form of a park's type (e.g., "National Park").

    Args:
        park_type_code (str): an abbreviated park type (e.g., "NP")

    Returns
        str: the full, human-legible park type
    """
    long_park_type = _PARK_TYPES.get(park_type_code)

    # The type may not be found in two cases: the "type" is actually multiple
    # types concatenated with an ampersand, or the park is one of the four
    # sporadic parks (see above for a list)
    if long_park_type is None:
        split_type_code = park_type_code.split(' ')
        # In the first case we simply need to apply further processing to
        # retrieve both types and remove the initial "National" from the second
        if len(split_type_code) > 1:
            long_park_type = ' '.join([
                _PARK_TYPES[split_type_code[0]],
                '&',
                _PARK_TYPES['N' + split_type_code[-1]].replace('National ', '')
            ])
        # In the second case we can just return the abbreviated park type,
        # since "Sporadic" adequately describes those parks
        else:
            long_park_type = park_type_code.title()

    return long_park_type
