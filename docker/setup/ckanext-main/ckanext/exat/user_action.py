# encoding: utf-8

import ckan.logic as logic
import ckan.logic.schema as schema_
import ckan.lib.uploader as uploader
import ckan.lib.navl.dictization_functions as dfunc
import ckan.lib.dictization.model_save as model_save
import ckan.lib.dictization.model_dictize as model_dictize

_get_or_bust = logic.get_or_bust
_check_access = logic.check_access
_validate = dfunc.validate
ValidationError = logic.ValidationError

def user_update(context, data_dict):
    model = context['model']
    user = author = context['user']
    session = context['session']
    schema = context.get('schema') or schema_.default_update_user_schema()
    id = _get_or_bust(data_dict, 'id')

    user_obj = model.User.get(id)
    context['user_obj'] = user_obj
    if user_obj is None:
        raise NotFound('User was not found.')

    _check_access('user_update', context, data_dict)

    upload = uploader.get_uploader('user')
    upload.update_data_dict(data_dict, 'image_url',
                            'image_upload', 'clear_upload')

    data, errors = _validate(data_dict, schema, context)
    if errors:
        session.rollback()
        raise ValidationError(errors)

    # user schema prevents non-sysadmins from providing password_hash
    if 'password_hash' in data:
        data['_password'] = data.pop('password_hash')

    user = model_save.user_dict_save(data, context)

    upload.upload(uploader.get_max_image_size())

    if not context.get('defer_commit'):
        model.repo.commit()

    author_obj = model.User.get(context.get('user'))
    include_plugin_extras = False
    if author_obj:
        include_plugin_extras = author_obj.sysadmin and 'plugin_extras' in data
    user_dict = model_dictize.user_dictize(
        user, context, include_plugin_extras=include_plugin_extras)

    return user_dict
