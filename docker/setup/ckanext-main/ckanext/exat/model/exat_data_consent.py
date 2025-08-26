# encoding: utf-8

from sqlalchemy import types, Column, Table
from six import text_type

from ckan.model import meta
from ckan.model import core
from ckan.model import domain_object
from sqlalchemy.ext.mutable import MutableDict
import datetime
import uuid

import logging
log = logging.getLogger(__name__)

__all__ = ['exat_data_consent_table', 'ExatDataConsent']


def make_uuid():
    return text_type(uuid.uuid4())

exat_data_consent_table = Table(
    'exat_data_consent', meta.metadata,
    Column('id', types.UnicodeText, primary_key=True, default=make_uuid),
    Column('username', types.UnicodeText, nullable=False, unique=True),
    Column('created', types.DateTime, default=datetime.datetime.utcnow)
)


class ExatDataConsent(domain_object.DomainObject):

    @classmethod
    def get_by_user_name(cls, user_name):
        query = meta.Session.query(cls).autoflush(False)
        query = query.filter(or_(cls.user_name == user_name))
        return query.first()


meta.mapper(ExatDataConsent, exat_data_consent_table)


def get_consent_by_user(username):
    from sqlalchemy.exc import ProgrammingError
    try:
        obj = meta.Session.query(ExatDataConsent).filter_by(username=username).first()
        if obj:
            return obj
    except ProgrammingError:
        meta.Session.rollback()
    return None


def set_user_consent(username):
    obj = meta.Session.query(ExatDataConsent).filter_by(username=username).first()
    if obj:
        return

    obj = ExatDataConsent()
    obj.username = username

    meta.Session.add(obj)
    meta.Session.commit()