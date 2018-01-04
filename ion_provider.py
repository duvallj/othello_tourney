# This file will provide backend/config stuff for
# loggin in with ion + flask_social
from requests import request

config = {
    'id': 'ion',
    'name': 'ion',
    'install': '',
    'module': 'ion_provider',
    'base_url': 'https://ion.tjhsst.edu/',
    'authorize_url': 'https://ion.tjhsst.edu/oauth/authorize',
    'access_token_url': 'https://ion.tjhsst.edu/oauth/token',
    'request_token_url': None,
    'access_token_method': 'POST',
    'request_token_params': {
        'scope': 'https://ion.tjhsst.edu/api/profile'
    }
}

def get_api(connection, **kwargs):
    print('ga', connection)
    if response:
        profile = request(
            'https://ion.tjhsst.edu/api/profile',
            params={'access_token', response.get('access_token', None)}
        ).json()
        return profile
    return None


def get_provider_user_id(response, **kwargs):
    print('gpui', response)
    if response:
        profile = request(
            'https://ion.tjhsst.edu/api/profile',
            params={'access_token', response.get('access_token', None)}
        ).json()
        return profile['id']
    return None

def get_connection_values(response, **kwargs):
    if not response:
        return None

    print('gcv', response)

    profile = request(
        'https://ion.tjhsst.edu/api/profile',
        params={'access_token', response.get('access_token', None)}
    ).json()

    return dict(
        provider_id=config['id'],
        provider_user_id=profile['id'],
        access_token=response['access_token'],
        secret=None,
        display_name=profile['ion_username'],
        full_name=profile['full_name'],
        profile_url='http://ion.tjhsst.edu/profile/%s' % profile['id'],
        image_url=profile['picture'],
        email=profile['tj_email']
    )

def get_token_pair_from_response(response):
    print('gtpfr', response)
    return dict(
        access_token=response.get('access_token', None),
        secret=None
    )
