# encoding: utf-8

import ckan.plugins as plugins
import ckan.plugins.toolkit as toolkit
from ckan.lib.plugins import DefaultTranslation
from ckanext.exat.views.exat import exat
from ckanext.exat import helpers as exh
from ckanext.exat.middleware import DataConsentMiddleware
from ckan.common import _, g

import ckanext.exat.action as exat_action
import ckanext.exat.user_action as exat_user_action

import logging
import os

log = logging.getLogger(__name__)

class ExatPlugin(plugins.SingletonPlugin, DefaultTranslation):
    plugins.implements(plugins.IConfigurer, inherit=True)
    plugins.implements(plugins.IClick)
    plugins.implements(plugins.ITranslation)
    plugins.implements(plugins.IBlueprint)
    plugins.implements(plugins.ITemplateHelpers)
    plugins.implements(plugins.IAuthenticator, inherit=True)
    plugins.implements(plugins.IActions)
    plugins.implements(plugins.IMiddleware)

    # IConfigurer
    def update_config(self, config_):
        toolkit.add_template_directory(config_, 'templates')
        toolkit.add_public_directory(config_, 'public')
        toolkit.add_public_directory(config_, 'fanstatic')
        toolkit.add_resource('fanstatic', 'exat')

        try:
            from ckan.lib.webassets_tools import add_public_path
        except ImportError:
            pass
        else:
            asset_path = os.path.join(
                os.path.dirname(__file__), 'fanstatic'
            )
            add_public_path(asset_path, '/')

        toolkit.add_ckan_admin_tab(
            config_, u'exat.admin_data_policy',
            _('เงื่อนไขการเข้าถึงข้อมูล'),
            icon="window-maximize"
        )

    # IClick
    def get_commands(self):
        from ckanext.exat.cli.exat import get_commands
        return get_commands()

    # IBlueprint
    def get_blueprint(self):
        return [exat]

    # ITemplateHelpers
    def get_helpers(self):
        return {
            'exat_is_personnel': exh.is_personnel,
            'exat_data_policy_info': exh.data_policy_info,
            'exat_show_statistic_on_main_page': exh.show_statistic_on_main_page,
            'exat_top_view_datasets': exh.top_view_datasets
            # 'exat_top_download_resources': exh.top_download_resources
        }

    # IAuthenticator
    def logout(self):
        try:
            userobj = g.userobj
            plugin_extras = userobj.plugin_extras
            if plugin_extras and 'exat' in plugin_extras:
                user_info = plugin_extras[u'exat'][u'user_info']
                user_id = user_info[u'user_id']
                login_date = user_info[u'login_date']
                login_time = user_info[u'login_time']

                client = exh.ext_client()
                client.logout(user_id, login_date, login_time)
        except Exception as e:
            log.error("Call logout from client error")
    
    # IActions
    def get_actions(self):
        action_functions = {
            u"exat_get_data_policy": exat_action.get_data_policy,
            u"exat_update_data_policy": exat_action.update_data_policy,
            u"exat_collaborated_datasets_for_user": exat_action.collaborated_datasets_for_user,
            u"exat_personnel_add": exat_action.personnel_add,
            u"exat_user_update": exat_user_action.user_update
        }
        return action_functions


    # IMiddleware
    def make_middleware(self, app, config):
        return DataConsentMiddleware(app, config)
