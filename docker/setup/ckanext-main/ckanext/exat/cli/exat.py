# encoding: utf-8

import os
import sys
import click
from ckan.cli import error_shout
import ckan.plugins.toolkit as toolkit
import ckan.model as model
from ckanext.exat import helpers as exh

import logging

log = logging.getLogger(__name__)


@click.command(u"exat-init")
def exat_init():
    _config_option_update()
    _default_organization_create()


@click.command(u"exat-create-organizations")
def exat_create_organizations():
    _default_organization_create()
    initial_organizations = _load_organizations_data()
    for org_data in initial_organizations:
        _organization_create(org_data)

    click.echo("Done.")


@click.command(u"exat-delete-organizations")
def exat_delete_organizations():
    initial_organizations = _load_organizations_data()
    for org_data in initial_organizations:
        _organization_delete(org_data)


def _config_option_update():
    try:
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

        data_dict = {
            u'ckan.site_title': 'การทางพิเศษแห่งประเทศไทย',
            u'ckan.site_logo': '/exat/images/LOGO-EXAT.png',
            u'ckan.homepage_style': '1',
            u'ckan.main_css': '/base/css/main.css',
            u'ckan.site_about': 'ระบบบริหารจัดการบัญชีข้อมูล (Directory Service) การทางพิเศษแห่งประเทศไทย',
            u'ckan.site_org_address': 'การทางพิเศษแห่งประเทศไทย อาคารศูนย์บริหารทางพิเศษ กทพ. เลขที่ 111 ถนนริมคลองบางกะปิ แขวงบางกะปิ เขตห้วยขวาง กรุงเทพมหานคร 10310',
            u'ckan.site_org_contact': 'โทรศัพท์ 0 2558 9800 แฟกซ์ 0 2558 9788-9',
            u'ckan.site_org_email': 'callcenter@exat.co.th',
            u'ckan.favicon': '/exat/images/exat-icon.png'
        }

        toolkit.get_action(u'config_option_update')(context, data_dict)
    except Exception as e:
        error_shout(e)


def _default_organization_create():
    try:
        exh.get_or_create_default_organization()
    except Exception as e:
        error_shout(e)   


def _organization_create(org_data):
    try:
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

        group_obj = model.Group.by_name(org_data[u'name'])
        if group_obj is None:
            result = toolkit.get_action('organization_create')(context, org_data)
            click.secho(u"Successfully created organization: %s" % result['name'],
                        fg=u'green', bold=True)
    except Exception as e:
        error_shout(e)


def _organization_delete(org_data):
    try:
        log.debug(org_data)
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

        group_obj = model.Group.by_name(org_data[u'name'])
        if group_obj:
            toolkit.get_action('organization_delete')(context, {'id': group_obj.id, 'name': org_data[u'name']})
            click.secho(u"Successfully delete organization: %s" % org_data['name'],
                        fg=u'green', bold=True)
    except Exception as e:
        error_shout(e)   


def _load_organizations_data():
    import json

    # Get the directory of the current script
    script_dir = os.path.dirname(os.path.abspath(__file__))

    # Specify the name of your JSON file
    file_name = 'organizations.json'

    # Construct the file path
    file_path = os.path.join(script_dir, file_name)

    # Open file
    with open(file_path, 'r') as file:
        data = json.load(file)

    return data
        

def get_commands():
    return [exat_init, exat_create_organizations, exat_delete_organizations]
