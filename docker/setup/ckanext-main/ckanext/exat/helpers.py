# encoding: utf-8

import logging
import string
import secrets

from importlib import import_module
from ckan.lib import base
from ckan.common import g, config, asbool, request
import ckan.model as model
import ckan.lib.dictization.model_dictize as model_dictize
import ckan.plugins.toolkit as toolkit
import ckan.logic.schema as schema_
from ckanext.exat.model.exat_info import get_exat_info
from ckanext.exat.model.exat_data_consent import get_consent_by_user
from ckanext.thai_gdc import helpers as thai_gdc_h
from ckanext.thai_gdc.model.opend import OpendModel


log = logging.getLogger(__name__)
opend_model = OpendModel()


def ext_client():
    security_center_client = config.get('ckanext.exat.security_center.client')
    module_name, class_name = security_center_client.rsplit(':', 1)
    module = import_module(module_name)
    ClientClass = getattr(module, class_name)

    client = ClientClass()
    return client


def generate_password():
    alphabet = string.ascii_letters + string.digits
    password = ''.join(secrets.choice(alphabet) for i in range(32))
    return password


def update_or_create_user(exat_user_dict, password):
    user_dict = _make_user_dict_for_create_or_update(exat_user_dict, password)
    user_name = user_dict[u'name'].lower()
    user_obj = model.User.by_name(user_name)
    if user_obj:
        activate_user_if_deleted(user_obj)
        user_dict[u'id'] = user_obj.id
        user_dict = _update_user(user_dict)
    else:
        user_dict = _create_user(user_dict)

    return _make_user_upate_or_create_result_dict(user_dict, exat_user_dict)


def _make_user_upate_or_create_result_dict(user_dict, exat_user_dict):
    if user_dict is None:
        return None

    data_dict = {
        u'user_id': user_dict[u'id'],
        u'user_name': user_dict[u'name'],
        u'department_code': exat_user_dict[u'department_code'],
        u'department_name': exat_user_dict[u'department_name']
    }
    return data_dict


def _make_user_dict_for_create_or_update(exat_user_dict, password):
    user_dict = {
        u'name': exat_user_dict[u'user_id'].lower(),
        u'fullname': exat_user_dict[u'full_name'],
        u'password': password,
        u'plugin_extras': {
            u'exat': {
                u'user_info': exat_user_dict
            }
        }
    }
    return user_dict


def _update_user(user_dict):
    # just ignore email validation
    schema = schema_.default_update_user_schema()
    schema['email'] = schema['apikey']

    context = {
        u'ignore_auth': True,
        u'schema': schema
    }

    try:
        return toolkit.get_action(u'exat_user_update')(context, user_dict)
    except Exception as e:
        log.error(e)

    return None


def _create_user(user_dict):
    # just ignore email validation
    schema = schema_.default_user_schema()
    schema['email'] = schema['apikey']

    context = {
        u'ignore_auth': True,
        u'schema': schema
    }

    try:
        return toolkit.get_action(u'user_create')(context, user_dict)
    except Exception as e:
        log.error(e)

    return None


def get_user_dict_by_name(name):
    user_obj = model.User.by_name(name)
    if user_obj:
        activate_user_if_deleted(user_obj)
    return None


def activate_user_if_deleted(user_obj):
    if not user_obj:
        return
    if user_obj.is_deleted():
        user_obj.activate()
        user_obj.commit()
        log.info(u'User {} reactivated', user_obj.name)


def organization_member_for_user_update(data_dict):
    # Look up default organization
    assign_default_organization = asbool(config.get('ckanext.exat.assign_default_organization', False))
    if assign_default_organization:
        default_group_id = get_or_create_default_organization()
        if default_group_id:
            if not organization_member_exist(default_group_id, data_dict[u'user_id']):
                _organization_member_create(data_dict[u'user_name'], default_group_id)

    # Look up personnel organization
    assign_personnel_organization = asbool(config.get('ckanext.exat.assign_personnel_organization', False))
    if (assign_personnel_organization):
        personnel_group_id = get_personnel_organization(data_dict[u'department_code'])
        if personnel_group_id:
            if not organization_member_exist(personnel_group_id, data_dict[u'user_id']):
                _organization_member_create(data_dict[u'user_name'], personnel_group_id)

    return data_dict


def organization_member_exist(group_id, user_id):
     # Look up existing member
    member = model.Session.query(model.Member).\
        filter(model.Member.table_name == 'user').\
        filter(model.Member.table_id == user_id).\
        filter(model.Member.group_id == group_id).\
        filter(model.Member.state == 'active').first()
    if member:
        return True

    return False


def get_personnel_organization(department_code):
    try:
        group_obj = model.Group.by_name(department_code)
        if group_obj:
            return group_obj.id
    except Exception as e:
        log.error("Some error occur")

    return None


def get_or_create_default_organization():
    try:
        group_obj = model.Group.by_name('exat')
        if group_obj:
            return group_obj.id
        else:
            return create_default_organization()
    except Exception as e:
        log.error("Some error occur")

    return None


def create_default_organization():
    org_data = {
        u'name': 'exat',
        u'title': 'การทางพิเศษแห่งประเทศไทย',
        u'description': '',
        u'image_url': '',
        u'groups': []
    }

    site_user = toolkit.get_action(u'get_site_user')({
        u'model': model,
        u'ignore_auth': True},
        {}
    )
    context = {
        u'model': model,
        u'session': model.Session,
        u'ignore_auth': True,
        u'user': site_user['name'],
    }

    result = toolkit.get_action('organization_create')(context, org_data)
    return result['id']


def _organization_member_create(user_name, group_id):
    data_dict = {
        'username': user_name,
        'role': u'member',
        'id': group_id
    }

    context = {
        u'ignore_auth': True
    }

    return toolkit.get_action(u'organization_member_create')(context, data_dict)

def is_personnel(user_name=None):
    user_obj = None
    if user_name:
        user_obj = model.User.by_name(user_name)
    else:
        user_obj = g.userobj

    if user_obj:
        plugin_extras = user_obj.plugin_extras
        if plugin_extras:
            return 'exat' in plugin_extras

    return False

def data_policy_info():
    show_policy = False
    request_path = request.path
    request_query_string = request.query_string
    data_policy_text = ""

    user_consent = get_consent_by_user(g.user)

    if user_consent is None:
        if request_path and request_path.startswith("/dataset"):
            data_policy_show = get_exat_info('data_policy.show', 'False')
            if data_policy_show and data_policy_show == 'True':
                show_policy = True
                data_policy_text = get_exat_info('data_policy.text', '')

    if request_query_string:
        request_path = request_path + "?" + request_query_string

    data_dict = {
        "data_policy_text": data_policy_text,
        "show_policy": show_policy,
        "request_path": request_path
    }

    return data_dict


def show_statistic_on_main_page():
    show = get_exat_info('statictic.show', 'False')
    return show


def top_view_datasets():
    popular_datasets = thai_gdc_h.get_popular_datasets(5)
    return popular_datasets


def top_download_resources():
    top_resources = opend_model.get_resource_download_top(5)

    return top_resources