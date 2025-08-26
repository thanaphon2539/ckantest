# encoding: utf-8

import logging
from collections import defaultdict
from datetime import datetime
import ckan.model as model

log = logging.getLogger(__name__)

def popular_datasets(limit = None):
    sql = '''
        select p."name" as "name", p.title as title, MAX(ts.recent_views) as recent_views
        from tracking_summary ts inner join package p on p.id = ts.package_id
        where p.state = 'active'
        group by p."name", p.title order by recent_views desc
    '''

    if limit is not None:
        sql = '''{} limit {}'''.format(sql, limit)

    resultproxy = model.Session.execute(sql)

    data = []
    for rowproxy in resultproxy:
        my_dict = {column: value for column, value in rowproxy.items()}
        data.append(my_dict)

    return data


def daily_view_datasets():
    sql = '''
        select 
            ts.tracking_date AS tracking_date,
            p."name" as "name", 
            p.title as title,
            ts.count,
            ts.recent_views as recent_views
        from tracking_summary ts inner join package p on p.id = ts.package_id
        where ts.tracking_date >= (SELECT MAX(tracking_date) FROM tracking_summary) - INTERVAL '30 days' and p.state = 'active'
        order by ts.tracking_date desc, p."name"
    '''

    resultproxy = model.Session.execute(sql)

    data = defaultdict(list)
    for rowproxy in resultproxy:
        tracking_date = rowproxy['tracking_date']
        dataset = {
            'name': rowproxy['name'],
            'title': rowproxy['title'],
            'count': rowproxy['count'],
            'recent_views': rowproxy['recent_views']
        }
        data[tracking_date].append(dataset)

    grouped_data = []
    for date, datasets in data.items():
        formatted_date = date.strftime('%d-%m-%Y')
        entry = {
            'date': date,
            'formatted_date': formatted_date,
            'datasets': datasets
        }
        grouped_data.append(entry)

    sorted_grouped_data = sorted(grouped_data, key=lambda x: (x['date'], x['datasets'][0]['name']), reverse=True)

    return sorted_grouped_data


def daily_download_resources():
    sql = '''
        select
            ts.tracking_date as tracking_date,
            pa."name" as package_name,
            pa.title as package_title,
            re.id as resource_id,
            re."name" as resource_name,
            re.format as resource_format,
            ts."count" as "count",
            ts.recent_views as recent_views,
            ts.url as url
        from tracking_summary ts
        inner join package pa on pa.id = replace(replace(substring(ts.url from '\/dataset\/.*\/resource\/'),'/dataset/',''),'/resource/','') 
        inner join resource re on re.id = replace(replace(substring(ts.url from '\/resource\/.*\/download\/'),'/resource/',''),'/download/','') 
        where 
            ts.tracking_type = 'resource'
            and ts.tracking_date >= (SELECT MAX(tracking_date) FROM tracking_summary) - INTERVAL '30 days'
            and re.state  = 'active'
            and pa.state = 'active'
    '''

    resultproxy = model.Session.execute(sql)

    data = defaultdict(list)
    for rowproxy in resultproxy:
        tracking_date = rowproxy['tracking_date']
        resource = {
            'package_name': rowproxy['package_name'],
            'package_title': rowproxy['package_title'],
            'resource_id': rowproxy['resource_id'],
            'resource_name': rowproxy['resource_name'],
            'resource_format': rowproxy['resource_format'],
            'count': rowproxy['count'],
            'recent_views': rowproxy['recent_views'],
            'url': rowproxy['url']
        }
        data[tracking_date].append(resource)

    grouped_data = []
    for date, resources in data.items():
        formatted_date = date.strftime('%d-%m-%Y')
        entry = {
            'date': date,
            'formatted_date': formatted_date,
            'resources': resources
        }
        grouped_data.append(entry)

    sorted_grouped_data = sorted(grouped_data, key=lambda x: (x['date'], x['resources'][0]['package_name']), reverse=True)

    return sorted_grouped_data