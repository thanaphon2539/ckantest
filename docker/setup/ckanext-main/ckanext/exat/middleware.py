# encoding: utf-8

import ckan.plugins.toolkit as toolkit
from ckan.common import asbool, g
from six.moves.urllib.parse import quote, parse_qs
from ckanext.exat.model.exat_data_consent import get_consent_by_user
from ckanext.exat.model.exat_info import get_exat_info

import logging


log = logging.getLogger(__name__)


class DataConsentMiddleware(object):
    def __init__(self, app, config):
        self.app = app


    def __call__(self, environ, start_response):
        show_policy = asbool(get_exat_info('data_policy.show', 'False'))
        if show_policy:
            path_info = environ['PATH_INFO']
            if path_info.startswith('/dataset'):
                if not self.has_accepted_consent(environ):
                    query_string = environ['QUERY_STRING']
                    if query_string:
                        path_info = '''{}?{}'''.format(path_info, query_string)

                    start_response('302 Found', [('Location', '/data-consent?r=' + quote(path_info)), ('Cache-Control', 'no-cache')])
                    return []

        return self.app(environ, start_response)


    def has_accepted_consent(self, environ):
        user = self.get_remote_user(environ)
        if user:
            user_consent = get_consent_by_user(user)
            if user_consent is None:
                return False
        else:
            consent_value = self.get_consent_cookie(environ)
            if consent_value is None:
                return False
        
        return True


    def get_remote_user(self, environ):
        if 'REMOTE_USER' in environ:
            return environ['REMOTE_USER']
        return None


    def get_consent_cookie(self, environ):
        try:
            cookie_header = environ.get('HTTP_COOKIE')
            if cookie_header:
                cookies = {}
                for c in cookie_header.split(';'):
                    key_value = c.strip().split('=')
                    key = key_value[0].strip()
                    value = '='.join(key_value[1:]).strip().strip('"')
                    cookies[key] = value
                cookie_value = cookies.get('udtp')
                return cookie_value
        except Exception as e:
            pass

        return None

