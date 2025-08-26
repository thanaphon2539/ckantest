# ckanext-exat

CKAN Extension เสริมการทำงานร่วมกับ CKAN Open-D ให้เหมาะกับการใช้งานภายในการทางพิเศษแห่งประเทศไทย (กทพ.)


## Requirements

ติดตั้งร่วมกับ CKAN Open-D (CKAN 2.9.5)


## Installation

ติดตั้ง CKAN Open-D:

1. [วิธีติดตั้ง CKAN Open-D](https://gitlab.nectec.or.th/opend/installing-ckan/-/blob/master/README.md)


ติดตั้ง ckanext-exat:

1. ทำการ activate CKAN virtual environment, เข่น:
```sh
     . /usr/lib/ckan/default/bin/activate
```

2. ทำการ clone โค้ดและติดตั้งบน virtualenv
```sh
    git clone git@git.sbpds.com:government/exat/common/ckanext.git ckanext-exat
    cd ckanext-exat
    pip install -e .
	pip install -r requirements.txt
```

3. แก้ไข config ไฟล์ของ CKAN โดยเพิ่ม plugin `exat` ไว้หน้า `thai_gdc` 
   (โดยปกติ config ไฟล์จะอยู่ที่ `/etc/ckan/default/ckan.ini`).
```sh
    ckan.plugins = ... exat thai_gdc ...
```

4. แก้ไข config ไฟล์ของ CKAN โดยเพิ่ม config สำหรับ extension ดังนี้
```sh
ckanext.exat.security_center.ws_endpoint = (url ของ webservice)
ckanext.exat.security_center.client = ckanext.exat.lib.security_center:SoapSecurityClient
ckanext.exat.assign_default_organization = True
```

5. Restart CKAN.
```sh
     sudo supervisorctl reload
```

## Developer installation

To install ckanext-exat for development, activate your CKAN virtualenv and
do:
```sh
    git clone git@git.sbpds.com:government/exat/common/ckanext.git ckanext-exat
    cd ckanext-exat
    python setup.py develop
    pip install -r dev-requirements.txt
```
