# encoding: utf-8

import logging
from ckanext.exat.lib.security_center import SecurityClient
from datetime import datetime

log = logging.getLogger(__name__)

_mock_users = [
    { 
        'user_id': '10001',
        'password': 'test1234',
        'user_data': { 
            'prefix': 'Mr.',
            'first_name': 'Peter',
            'last_name': 'Bishop',
            'department_code': 'a001',
            'department_name': 'Dep 1',
            'position': 'programmer'
        }
    },
    { 
        'user_id': '10002',
        'password': 'test1234',
        'user_data': { 
            'prefix': 'Mrs.',
            'first_name': 'Olivia',
            'last_name': 'Dunham',
            'department_code': 'a002',
            'department_name': 'Dep 2',
            'position': 'analyst'
        }
    },
    { 
        'user_id': '10003',
        'password': 'test1234',
        'user_data': { 
            'prefix': 'Mr.',
            'first_name': 'Walter',
            'last_name': 'Bishop',
            'department_code': 'a003',
            'department_name': 'Dep 3',
            'position': 'scientist'
        }
    }
]

class MockSecurityClient(SecurityClient):

    def authenticate(self, user_id, user_password):
        user_data = self._get_user_data(user_id, user_password)
        if user_data:
            now = datetime.now()
            login_date = now.date().strftime("%Y-%m-%d")
            login_time = now.time().strftime("%H:%M:%S")
            return {
                u'user_id': user_id,
                u'full_name': '{} {} {}'.format(user_data['prefix'], user_data['first_name'], user_data['last_name']),
                u'department_code': user_data['department_code'],
                u'department_name': user_data['department_name'],
                u'position': user_data['position'],
                u'result_code': 0,
                u'result_text': 'success',
                u'login_date': login_date,
                u'login_time': login_time
            }

        return {
                u'user_id': None,
                u'full_name': None,
                u'department_code': None,
                u'department_name': None,
                u'position': None,
                u'result_code': 9,
                u'result_text': u'รหัสไม่ถูกต้อง',
                u'login_date': None,
                u'login_time': None
            }


    def logout(self, user_id, login_date, login_time):
        return None


    def change_password(self, user_id, old_password, new_password1, new_password2):
        return None
    

    def _get_user_data(self, user_id, password):
        for user in _mock_users:
            if user['user_id'] == user_id and user['password'] == password:
                return user['user_data']
        return None

    def user_info(self, user_id):
        user_data = self._get_user_data(user_id, user_password)
        if user_data:
            now = datetime.now()
            login_date = now.date().strftime("%Y-%m-%d")
            login_time = now.time().strftime("%H:%M:%S")
            return {
                u'user_id': user_id,
                u'full_name': '{} {} {}'.format(user_data['prefix'], user_data['first_name'], user_data['last_name']),
                u'department_code': user_data['department_code'],
                u'department_name': user_data['department_name'],
                u'position': user_data['position'],
                u'result_code': 0,
                u'result_text': 'success',
                u'login_date': login_date,
                u'login_time': login_time
            }

        return None