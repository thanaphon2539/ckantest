# encoding: utf-8

import ckan.plugins.toolkit as toolkit
import ckan.lib.navl.dictization_functions as df
from ckanext.exat.model.exat_info import get_exat_info, set_exat_info
import ckan.model as model
from ckanext.exat import helpers as exh

import logging
log = logging.getLogger(__name__)


def get_data_policy(context, data_dict):
    data_dict = {
        "data_policy_text": get_exat_info('data_policy.text', ''),
        "data_policy_show": get_exat_info('data_policy.show', 'False')
    }

    return data_dict


def update_data_policy(context, data_dict):
    schema = _data_policy_schema()
    data, errors = df.validate(data_dict, schema, context)
    if errors:
        raise toolkit.ValidationError(errors)

    data_policy_text = data["data_policy_text"]
    data_policy_show = data["data_policy_show"]

    set_exat_info("data_policy.text", data_policy_text)
    set_exat_info("data_policy.show", data_policy_show)

    return data


def _data_policy_schema():
    schema = {
        "data_policy_text": [toolkit.get_validator("not_empty"), unicode],
        "data_policy_show": [toolkit.get_validator("not_empty"), unicode],
    }
    return schema


def collaborated_datasets_for_user(context, data_dict):
    try:
        toolkit.check_access(u'sysadmin', context)
    except toolkit.NotAuthorized:
        toolkit.abort(403, _(u'Need to be system administrator to administer'))

    user_id = toolkit.get_or_bust(data_dict, 'id')
    user = model.User.get(user_id)
    if not user:
        raise toolkit.NotAuthorized(_('Not allowed to retrieve collaborators'))

    sql = '''
        select p.id as package_id , p.name as package_name, pm.user_id, pm.capacity from package_member pm 
        inner join package p on pm.package_id = p.id
        where pm.user_id = '{}'
    '''.format(user.id)

    resultproxy = model.Session.execute(sql)
    data = []
    for rowproxy in resultproxy:
        my_dict = {column: value for column, value in rowproxy.items()}
        my_dict.update({u"user_name": user.name})
        data.append(my_dict)

    return data


def personnel_add(context, data_dict):
    schema = _personnel_add_schema()
    data, errors = df.validate(data_dict, schema, context)
    if errors:
        raise toolkit.ValidationError(errors)

    # return exists one
    employee_id = data['employee_id']
    username = employee_id.lower()
    user = model.User.by_name(username)
    if user:
        data = {
            u'username': user.name,
            u'is_new': False
        }
        return data

    # add new from Security Center
    client = exh.ext_client()
    result_dict = client.user_info(employee_id)
    if result_dict:
        result_code = result_dict[u'result_code']
        if result_code == 0:
            # try to create new user
            password = exh.generate_password()
            user_dict = exh.update_or_create_user(result_dict, password)
            if user_dict:
                data = {
                    u'username': user_dict['user_name'],
                    u'is_new': True
                }
                return data

    errors = {
        u'employee_id': [u'ไม่พบข้อมูลบุคคลากร']
    }
    raise toolkit.ValidationError(errors)


def _personnel_add_schema():
    schema = {
        "employee_id": [toolkit.get_validator("not_empty"), unicode],
    }
    return schema
