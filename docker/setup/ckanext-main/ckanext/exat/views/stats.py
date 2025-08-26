# encoding: utf-8

from flask.views import MethodView
import logging
import time

import ckan.plugins.toolkit as toolkit
import ckanext.dga_stats.stats as stats_lib
import ckanext.exat.stats as exat_stats

log = logging.getLogger(__name__)


class ExatStatsView(MethodView):
    def timed(self, f, arg = None):
        if arg:
            ret = f(arg)
        else:
            ret = f()
        return ret


    def get(self):
        stats = stats_lib.Stats()

        extra_vars = {
            u'summary_stats': self.timed(stats.summary_stats),
            u'top_tags': self.timed(stats.top_tags),
            u'largest_groups': self.timed(stats.largest_groups),
            u'res_by_org': self.timed(stats.res_by_org),
            u'by_org': self.timed(stats.by_org),
            u'top_package_owners': self.timed(stats.top_package_owners),
            u'most_edited_packages': self.timed(stats.most_edited_packages),
            u'recent_updated_datasets': self.timed(stats.recent_updated_datasets),
            u'recent_created_datasets': self.timed(stats.recent_created_datasets),
            u'user_access_list': self.timed(stats.user_access_list),
            u'users_by_organisation': self.timed(stats.users_by_organisation),
            u'popular_datasets': exat_stats.popular_datasets(),
            u'daily_view_datasets': exat_stats.daily_view_datasets(),
            u'daily_download_resources': exat_stats.daily_download_resources()
        }

        return toolkit.render('exat/exat_stats.html', extra_vars)
