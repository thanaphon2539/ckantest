# encoding: utf-8

from sqlalchemy import types, Column, Table
from six import text_type

from ckan.model import meta
from ckan.model import core
from ckan.model import domain_object


__all__ = ['exat_info_table', 'ExatInfo', 'get_exat_info', 'delete_exat_info', 'set_exat_info']


exat_info_table = Table(
    'exat_info', meta.metadata,
    Column('id', types.Integer(),  primary_key=True, nullable=False),
    Column('key', types.Unicode(100), unique=True, nullable=False),
    Column('value', types.UnicodeText),
)


class ExatInfo(core.StatefulObjectMixin,
                 domain_object.DomainObject):

    def __init__(self, key, value):

        super(ExatInfo, self).__init__()

        self.key = key
        self.value = text_type(value)


meta.mapper(ExatInfo, exat_info_table)


def get_exat_info(key, default=None):
    ''' get data from exat_info table '''
    from sqlalchemy.exc import ProgrammingError
    try:
        obj = meta.Session.query(ExatInfo).filter_by(key=key).first()
        if obj:
            return obj.value
    except ProgrammingError:
        meta.Session.rollback()
    except Exception:
        pass

    return default


def delete_exat_info(key, default=None):
    ''' delete data from exat_info table '''
    obj = meta.Session.query(ExatInfo).filter_by(key=key).first()
    if obj:
        meta.Session.delete(obj)
        meta.Session.commit()


def set_exat_info(key, value):
    ''' save data in the exat_info table '''
    obj = None
    obj = meta.Session.query(ExatInfo).filter_by(key=key).first()
    if obj and obj.value == text_type(value):
        return
    if not obj:
        obj = ExatInfo(key, value)
    else:
        obj.value = text_type(value)

    meta.Session.add(obj)
    meta.Session.commit()
    return True