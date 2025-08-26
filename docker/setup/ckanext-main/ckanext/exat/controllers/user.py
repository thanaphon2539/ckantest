import ckan.plugins.toolkit as toolkit
import logging

log = logging.getLogger(__name__)

class ExatUserController(toolkit.BaseController):
    def login(self):
        log.info("TEST::")
        return toolkit.render('exat/login.html')