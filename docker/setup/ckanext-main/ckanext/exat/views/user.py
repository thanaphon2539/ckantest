# encoding: utf-8

from flask.views import MethodView
import logging
from ckan.common import asbool
from ckan.views.user import EditView, set_repoze_user, _extra_template_variables

import ckan.lib.authenticator as authenticator
import ckan.lib.base as base
import ckan.plugins.toolkit as toolkit
import ckan.lib.helpers as h
import ckan.lib.navl.dictization_functions as dictization_functions
import ckan.logic as logic
import ckan.logic.schema as schema
import ckan.model as model
from ckan.common import _, config, g, request
from ckanext.exat import helpers as exh

log = logging.getLogger(__name__)

def _ckeck_sysadmin_access(context):
    try:
        toolkit.check_access(u'sysadmin', context)
    except toolkit.NotAuthorized:
        toolkit.abort(403, _(u'Need to be system administrator to administer'))

class ExatEditView(EditView):

    def post(self, id=None):
        context, id = self._prepare(id)
        if not context[u'save']:
            return self.get(id)

        if id in (g.userobj.id, g.userobj.name):
            current_user = True
        else:
            current_user = False
        old_username = g.userobj.name

        try:
            data_dict = logic.clean_dict(
                dictization_functions.unflatten(
                    logic.tuplize_dict(logic.parse_params(request.form))))
            data_dict.update(logic.clean_dict(
                dictization_functions.unflatten(
                    logic.tuplize_dict(logic.parse_params(request.files))))
            )

        except dictization_functions.DataError:
            base.abort(400, _(u'Integrity Error'))
        data_dict.setdefault(u'activity_streams_email_notifications', False)

        context[u'message'] = data_dict.get(u'log_message', u'')
        data_dict[u'id'] = id
        email_changed = data_dict[u'email'] != g.userobj.email

        if (data_dict[u'password1']
                and data_dict[u'password2']) or email_changed:
            identity = {
                u'login': g.user,
                u'password': data_dict[u'old_password']
            }
            auth = authenticator.UsernamePasswordAuthenticator()

            if auth.authenticate(request.environ, identity) != g.user:
                errors = {
                    u'oldpassword': [_(u'Password entered was incorrect')]
                }
                error_summary = {_(u'Current Password'): _(u'incorrect password')}\
                    if not g.userobj.sysadmin \
                    else {_(u'Sysadmin Password'): _(u'incorrect password')}
                return self.get(id, data_dict, errors, error_summary)

        try:
            user = logic.get_action(u'user_update')(context, data_dict)
        except logic.NotAuthorized:
            base.abort(403, _(u'Unauthorized to edit user %s') % id)
        except logic.NotFound:
            base.abort(404, _(u'User not found'))
        except logic.ValidationError as e:
            errors = e.error_dict
            error_summary = e.error_summary
            return self.get(id, data_dict, errors, error_summary)

        h.flash_success(_(u'Profile updated'))
        resp = h.redirect_to(u'user.read', id=user[u'name'])
        if current_user and data_dict[u'name'] != old_username:
            # Changing currently logged in user's name.
            # Update repoze.who cookie to match
            set_repoze_user(data_dict[u'name'], resp)
        return resp

    
    def get(self, id=None, data=None, errors=None, error_summary=None):
        context, id = self._prepare(id)
        data_dict = {u'id': id}
        is_personnel = False
        try:
            old_data = logic.get_action(u'user_show')(context, data_dict)

            g.display_name = old_data.get(u'display_name')
            g.user_name = old_data.get(u'name')
            data = data or old_data

            is_personnel = exh.is_personnel(g.user_name)

        except logic.NotAuthorized:
            base.abort(403, _(u'Unauthorized to edit user %s') % u'')
        except logic.NotFound:
            base.abort(404, _(u'User not found'))
        user_obj = context.get(u'user_obj')

        errors = errors or {}
        vars = {
            u'data': data,
            u'errors': errors,
            u'error_summary': error_summary,
            u'is_personnel': is_personnel
        }

        extra_vars = _extra_template_variables({
            u'model': model,
            u'session': model.Session,
            u'user': g.user
        }, data_dict)

        extra_vars[u'show_email_notifications'] = asbool(
            config.get(u'ckan.activity_streams_email_notifications'))
        vars.update(extra_vars)
        extra_vars[u'form_vars'] = vars

        return toolkit.render(u'user/edit.html', extra_vars)


class UserCollaboratedDatasetsView(MethodView):
    def get(self, id):
        context = {
            u'model': model,
            u'session': model.Session,
            u'user': g.user,
            u'auth_user_obj': g.userobj,
            u'for_view': True,
            u'include_plugin_extras': True
        }

        data_dict = {
            u'id': id,
            u'user_obj': g.userobj,
            u'include_datasets': True,
            u'include_num_followers': True
        }

        _ckeck_sysadmin_access(context)

        collaborators = toolkit.get_action('exat_collaborated_datasets_for_user')(context, data_dict)

        extra_vars = _extra_template_variables(context, data_dict)
        extra_vars.update({u'collaborators': collaborators})

        return toolkit.render('user/collaborated_datasets/collaborated_datasets.html', extra_vars)

    
class UserCollaboratedDatasetEditView(MethodView):
    def get(self, id):
        context = {
            u'model': model,
            u'session': model.Session,
            u'user': g.user,
            u'auth_user_obj': g.userobj,
            u'for_view': True,
            u'include_plugin_extras': True
        }
        

        data_dict = {
            u'id': id,
            u'user_obj': g.userobj,
            u'include_datasets': True,
            u'include_num_followers': True
        }

        _ckeck_sysadmin_access(context)

        extra_vars = _extra_template_variables(context, data_dict)

        return toolkit.render('user/collaborated_datasets/collaborated_dataset_new.html', extra_vars)   

    def post(self, id):
        context = {u'model': model, u'user': g.user}

        _ckeck_sysadmin_access(context)

        try:
            form_dict = logic.clean_dict(
                    dictization_functions.unflatten(
                        logic.tuplize_dict(
                            logic.parse_params(request.form))))

            dataset_name = form_dict['dataset']
            dataset = model.Package.get(dataset_name)
            if dataset is None:
                h.flash_error(_(u'Dataset not found'))
                return h.redirect_to(u'exat.collaborated_dataset_new', id=id)

            data_dict = {
                u'id': dataset.name,
                u'user_id': id,
                u'capacity': 'member'
            }

            toolkit.get_action('package_collaborator_create')(context, data_dict)

        except Exception as e:
            h.flash_error(_(u'Some error occur'))
            return h.redirect_to(u'exat.collaborated_dataset_new', id=id)

        return h.redirect_to(u'exat.collaborated_datasets', id=id)

