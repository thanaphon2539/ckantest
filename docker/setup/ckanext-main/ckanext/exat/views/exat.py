# encoding: utf-8

import logging

from flask import Blueprint, make_response, redirect
import ckan.plugins.toolkit as toolkit
import ckan.lib.helpers as h
import ckan.lib.search as search
import ckan.model as model
from ckan.views.user import set_repoze_user
from ckan.common import _, config, g, request, asbool
from ckanext.exat import helpers as exh
from ckanext.exat.views.user import ExatEditView, UserCollaboratedDatasetsView, UserCollaboratedDatasetEditView
from ckanext.exat.views.stats import ExatStatsView
from ckanext.exat.model.exat_data_consent import set_user_consent, get_consent_by_user
from ckanext.exat.model.exat_info import get_exat_info


log = logging.getLogger(__name__)
exat = Blueprint(u'exat', __name__)


def home_index():
    u'''display home page'''
    try:
        context = {u'model': model, u'session': model.Session,
                   u'user': g.user, u'auth_user_obj': g.userobj}
        data_dict = {u'q': u'*:*',
                     u'facet.field': h.facets(),
                     u'rows': 4,
                     u'start': 0,
                     u'sort': u'view_recent desc',
                     u'fq': u'capacity:"public"'}
        query = toolkit.get_action(u'package_search')(context, data_dict)
        g.search_facets = query['search_facets']
        g.package_count = query['count']
        g.datasets = query['results']

        g.facet_titles = {
            u'organization': _(u'Organizations'),
            u'groups': _(u'Groups'),
            u'tags': _(u'Tags'),
            u'res_format': _(u'Formats'),
            u'license': _(u'Licenses'),
        }

    except search.SearchError:
        g.package_count = 0

    if g.userobj and not g.userobj.email and not exh.is_personnel():
        url = h.url_for(controller=u'user', action=u'edit')
        msg = _(u'Please <a href="%s">update your profile</a>'
                u' and add your email address. ') % url + \
            _(u'%s uses your email address'
                u' if you need to reset your password.') \
            % config.get(u'ckan.site_title')
        h.flash_notice(msg, allow_html=True)
    return toolkit.render(u'home/index.html', extra_vars={})


def me():
    return h.redirect_to(
        config.get(u'ckan.route_after_login', u'dashboard.index'))


def login():
    if g.user:
        return toolkit.render(u'exat/logout_first.html')

    return toolkit.render('exat/login.html')


def post_login():
    g.user = None
    g.userobj = None

    identity = _get_identity()
    result_dict = _authenticate(identity)
    g.user = result_dict[u'user']
    if g.user is None:
        err = result_dict[u'result_text']
        h.flash_error(err)
        return login()

    g.userobj = model.User.by_name(g.user)    
    resp = me()

     # Log user into Ckan <= 2.9.5, identifies the user only using the internal id.
    set_repoze_user(g.user, resp)
    
    return resp


def change_password():
    return toolkit.render('exat/change_password.html')


def post_change_password():
    login = request.form.get(u'login')
    old_password = request.form.get(u'old_password')
    password1 = request.form.get(u'password1')
    password2 = request.form.get(u'password2')

    client = exh.ext_client()
    result_dict = client.change_password(login, old_password, password1, password2)
    if result_dict:
        result_code = result_dict[u'result_code']
        result_text = result_dict[u'result_text']
        if result_code == 0:
            h.flash_success(result_text)
            return change_password()
        else:
            h.flash_error(result_text)
            return change_password()

    h.flash_error('Change Password Failed')
    return change_password()


def _get_identity():
    identity = {
        u'login': request.form.get(u'login'),
        u'password': request.form.get(u'password')
    }
    return identity


def _authenticate(identity):
    user_id = identity[u'login']
    password = identity[u'password']

    result_dict = {
        u'user': None,
        u'result_code': 2,
        u'result_text': _(u'Login failed. Bad username or password.')
    }

    client = exh.ext_client()
    exat_user_dict = client.authenticate(user_id, password)
    if exat_user_dict:
        result_dict[u'result_code'] = exat_user_dict['result_code']
        result_dict[u'result_text'] = exat_user_dict['result_text']
        if exat_user_dict['result_code'] == 0:
            user = _process_user(exat_user_dict, password)
            result_dict[u'user'] = user

    return result_dict


def _process_user(exat_user_dict, password):
    user_dict = exh.update_or_create_user(exat_user_dict, password)
    if user_dict is None:
        return None

    user_dict = exh.organization_member_for_user_update(user_dict)

    return user_dict[u'user_name']


def _ckeck_sysadmin_access(context):
    try:
        toolkit.check_access(u'sysadmin', context)
    except toolkit.NotAuthorized:
        toolkit.abort(403, _(u'Need to be system administrator to administer'))


def admin_data_policy():
    context = dict(model=model, user=g.user, auth_user_obj=g.userobj)
    _ckeck_sysadmin_access(context)

    data = toolkit.get_action("exat_get_data_policy")(context)

    errors = {}
    error_summary = {}
    extra_vars = {'data': data, 'errors': errors, 'error_summary': error_summary}
    return toolkit.render('admin/data_policy.html', extra_vars=extra_vars)


def post_admin_data_policy():
    context = dict(model=model, user=g.user, auth_user_obj=g.userobj)
    _ckeck_sysadmin_access(context)

    data = {
        "data_policy_text": request.form.get(u'data_policy_text'),
        "data_policy_show": request.form.get(u'data_policy_show')
    }

    errors = None
    error_summary = None

    try:
        data = toolkit.get_action("exat_update_data_policy")(context, data)
    except toolkit.ValidationError as e:
        errors = e.error_dict
        error_summary = e.error_summary
        extra_vars = {'data': data, 'errors': errors, 'error_summary': error_summary}
        return toolkit.render('admin/data_policy.html', extra_vars=extra_vars)

    return toolkit.redirect_to("/ckan-admin/data-policy")


def accept_data_policy():
    redirect_path = request.form.get(u'redirect_path') or '/dataset'

    response = make_response(redirect(redirect_path))
    response.set_cookie(
        'udtp',
        value=exh.generate_password(),
        path='/',
        secure=False,
        httponly=True
    )

    if g.user:
        set_user_consent(g.user)

    # return toolkit.redirect_to(redirect_path)
    return response


def collaborated_dataset_delete(user_id, package_id):
    context = {
        u'model': model,
        u'session': model.Session,
        u'user': g.user,
        u'auth_user_obj': g.userobj
    }

    data_dict = {
        u'id': package_id,
        u'user_id': user_id
    }

    toolkit.get_action('package_collaborator_delete')(context, data_dict)

    return toolkit.redirect_to(u'/user/{}/collaborated_datasets'.format(user_id))


def data_consent():
    redirect_path = request.params.get('r', '/dataset')
    show_policy = asbool(get_exat_info('data_policy.show', 'False'))
    if show_policy:
        user_consent = get_consent_by_user(g.user)
        if user_consent is None:
            data_policy_text = get_exat_info('data_policy.text', '')
            extra_vars = {'redirect_path': redirect_path, 'data_policy_text': data_policy_text}
            return toolkit.render('exat/data_consent.html', extra_vars=extra_vars)

    return toolkit.redirect_to(redirect_path)


def personnel_add():
    context = dict(model=model, user=g.user, auth_user_obj=g.userobj)
    _ckeck_sysadmin_access(context)

    errors = {}
    error_summary = {}
    extra_vars = {'errors': errors, 'error_summary': error_summary}
    return toolkit.render(u'exat/personnel_add.html', extra_vars=extra_vars)


def post_personnel_add():
    context = dict(model=model, user=g.user, auth_user_obj=g.userobj)
    _ckeck_sysadmin_access(context)

    data = {
        "employee_id": request.form.get(u'employee_id')
    }

    errors = None
    error_summary = None

    try:
        data = toolkit.get_action("exat_personnel_add")(context, data)
    except toolkit.ValidationError as e:
        errors = e.error_dict
        error_summary = e.error_summary
        extra_vars = {'data': data, 'errors': errors, 'error_summary': error_summary}
        return toolkit.render('exat/personnel_add.html', extra_vars=extra_vars)

    if data[u'is_new']:
        h.flash_success(u'เพิ่มบุคลากรสำเร็จ')
    else:
        h.flash_notice(u'บุคลากรมีการลงทะเบียนแล้ว')

    return toolkit.redirect_to("/user/" + data[u'username'])


# add url rules
exat.add_url_rule(u'/', view_func=home_index, methods=[u'GET'])
exat.add_url_rule(u'/exat/login', view_func=login, methods=[u'GET'])
exat.add_url_rule(u'/exat/login', view_func=post_login, methods=[u'POST'])
exat.add_url_rule(u'/exat/change_password', view_func=change_password, methods=[u'GET'])
exat.add_url_rule(u'/exat/change_password', view_func=post_change_password, methods=[u'POST'])

exat.add_url_rule(u'/exat/personnel/add', view_func=personnel_add, methods=[u'GET'])
exat.add_url_rule(u'/exat/personnel/add', view_func=post_personnel_add, methods=[u'POST'])

exat.add_url_rule(u'/data-consent', view_func=data_consent, methods=[u'GET'])

exat.add_url_rule(u'/ckan-admin/data-policy', view_func=admin_data_policy, methods=[u'GET'])
exat.add_url_rule(u'/ckan-admin/data-policy', view_func=post_admin_data_policy, methods=[u'POST'])
exat.add_url_rule(u'/exat/data-policy/accept', view_func=accept_data_policy, methods=[u'POST'])

_edit_view = ExatEditView.as_view(str(u'edit'))
exat.add_url_rule(u'/user/edit', view_func=_edit_view)
exat.add_url_rule(u'/user/edit/<id>', view_func=_edit_view)

_user_collaborated_datasets_view = UserCollaboratedDatasetsView.as_view(str(u'collaborated_datasets'))
exat.add_url_rule(u'/user/<id>/collaborated_datasets', view_func=_user_collaborated_datasets_view)

_user_collaborated_dataset_edit_view = UserCollaboratedDatasetEditView.as_view(str(u'collaborated_dataset_new'))
exat.add_url_rule(u'/user/<id>/collaborated_datasets/new', view_func=_user_collaborated_dataset_edit_view)

exat.add_url_rule(u'/user/<user_id>/collaborated_datasets/<package_id>/delete', view_func=collaborated_dataset_delete, methods=[u'POST'])

override_stats = asbool(config.get('ckanext.exat.override_stats', False))
if override_stats:
    _stats_view = ExatStatsView.as_view(str(u'site_stats'))
    exat.add_url_rule(u'/site_stats', view_func=_stats_view)
