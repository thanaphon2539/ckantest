# encoding: utf-8

import xml.etree.ElementTree as ET
import requests
from ckan.common import g, config

import logging

log = logging.getLogger(__name__)

class SecurityClient:
    def authenticate(self, user_id, user_password):
        raise NotImplementedError

    def logout(self, user_id, login_date, login_time):
        raise NotImplementedError

    def change_password(self, user_id, old_password, new_password1, new_password2):
        raise NotImplementedError

    def user_info(self, user_id):
        raise NotImplementedError


class SoapSecurityClient(SecurityClient):
    def authenticate(self, user_id, user_password):

        encrypted_password = self._password_encrypt(user_password)
        if encrypted_password is None:
            return None

        soap_request = self._make_authenticate_request(user_id, encrypted_password)
        soap_response = self._invoke_service('SecurityCenter', soap_request)
        if soap_response:
            data_dict = self._parse_authenticate_response(soap_response)
            return data_dict

        return None


    def logout(self, user_id, login_date, login_time):
        soap_request = self._make_logout_request(user_id, login_date, login_time)
        soap_response = self._invoke_service('SaveTime_Logout', soap_request)
        if soap_response:
            data_dict = self._parse_logout_response(soap_response)
            return data_dict

        return None


    def change_password(self, user_id, old_password, new_password1, new_password2):
        encrypted_password = self._password_encrypt(old_password)
        if encrypted_password is None: 
            return None

        soap_request = self._make_change_password_request(user_id, encrypted_password, new_password1, new_password2)
        soap_response = self._invoke_service('ChangePassword', soap_request)
        if soap_response:
            data_dict = self._parse_change_password_response(soap_response)
            return data_dict

        return None

    
    def user_info(self, user_id):
        soap_request = self._make_get_user_info_request(user_id)
        soap_response = self._invoke_service('GetUserDetail', soap_request)
        if soap_response:
            data_dict = self._parse_get_user_info_response(soap_response)
            return data_dict

        return None

    
    def _password_encrypt(self, password):
        try:
            soap_request = self._make_password_encrypt_request(password)
            soap_response = self._invoke_service('PasswordEncrypt', soap_request)
            if soap_response:
                data_dict = self._parse_password_encrypt_response(soap_response)
                result_code = data_dict[u'result_code']
                if result_code == 0:
                    return data_dict[u'encrpty_password']
        except Exception as e:
            return None
        
        return None


    def _invoke_service(self, service_name, soap_request):
        headers = {
            'Content-Type': 'text/xml'
        }

        try:
            url = self._get_ws_endpoint(service_name)
            response = requests.post(url, data=soap_request, headers=headers)
            soap_response = response.content.decode('utf-8')
            return soap_response
        except Exception as e:
            return None


    def _get_ws_endpoint(self, service_name):
        ws_endpoint = config.get('ckanext.exat.security_center.ws_endpoint')
        return "{}/{}.do".format(ws_endpoint, service_name)


    def _get_exat_sysid(self):
        return 'DCM'


    def _get_exat_soap_ip(self):
        return '127.0.0.1'


    def _make_authenticate_request(self, user_id, encrypt_password):
        sysid = self._get_exat_sysid()
        ip = self._get_exat_soap_ip()

        ns = {
            'xmlns:SOAP-ENV': 'http://schemas.xmlsoap.org/soap/envelope/'
        }

        envelope = ET.Element('SOAP-ENV:Envelope', ns)
        header = ET.SubElement(envelope, 'SOAP-ENV:Header')
        body = ET.SubElement(envelope, 'SOAP-ENV:Body')
        security_param = ET.SubElement(body, 'Security_Param')
        data = ET.SubElement(security_param, 'Data')

        ET.SubElement(data, 'U_ID').text = user_id
        ET.SubElement(data, 'U_Pass').text = encrypt_password
        ET.SubElement(data, 'SYSID').text = sysid
        ET.SubElement(data, 'IP').text = ip

        sopa_request = ET.tostring(envelope).decode()

        return sopa_request


    def _parse_authenticate_response(self, soap_response):
        if soap_response is None:
            return None

        try:
            root = ET.fromstring(soap_response)

            # Find the relevant elements in the SOAP response and extract the required information
            data_element = root.find('.//EXAT_SecurityCenter/Data')
            user_id = data_element.findtext('U_ID')
            prefix = data_element.findtext('U_Prefix')
            fname = data_element.findtext('U_Fname')
            lname = data_element.findtext('U_Lname')
            depart_code = data_element.findtext('U_DepartCode')
            depart_text = data_element.findtext('U_DepartText')
            position = data_element.findtext('U_Position')
            result_code = data_element.findtext('ResultCode')
            result_text = data_element.findtext('ResultText')
            login_date = data_element.findtext('U_DateLogin')
            login_time = data_element.findtext('U_TimeLogin')

            # Create the data_dict using the extracted information
            data_dict = {
                u'user_id': user_id,
                u'full_name': '{} {} {}'.format(prefix, fname, lname),
                u'department_code': depart_code,
                u'department_name': depart_text,
                u'position': position,
                u'result_code': int(result_code),
                u'result_text': result_text,
                u'login_date': login_date,
                u'login_time': login_time
            }

            return data_dict
        except Exception as e:
            return None
        

    def _make_change_password_request(self, user_id, encrypt_old_password, new_password1, new_password2):
        sysid = self._get_exat_sysid()

        ns = {
            'xmlns:SOAP-ENV': 'http://schemas.xmlsoap.org/soap/envelope/'
        }

        envelope = ET.Element('SOAP-ENV:Envelope', ns)
        header = ET.SubElement(envelope, 'SOAP-ENV:Header')
        body = ET.SubElement(envelope, 'SOAP-ENV:Body')
        security_param = ET.SubElement(body, 'Security_Param')
        data = ET.SubElement(security_param, 'Data')

        ET.SubElement(data, 'U_ID').text = user_id
        ET.SubElement(data, 'O_Pass').text = encrypt_old_password
        ET.SubElement(data, 'N_Pass').text = new_password1
        ET.SubElement(data, 'N_Pass2').text = new_password2
        ET.SubElement(data, 'SYSID').text = sysid

        sopa_request = ET.tostring(envelope).decode()

        return sopa_request

    
    def _parse_change_password_response(self, soap_response):
        if soap_response is None:
            return None

        try:
            root = ET.fromstring(soap_response)

            # Find the relevant elements in the SOAP response and extract the required information
            data_element = root.find('.//EXAT_SecurityCenter/Data')
            user_id = data_element.findtext('U_ID')
            result_code = data_element.findtext('ResultCode')
            result_text = data_element.findtext('ResultText')

            # Create the data_dict using the extracted information
            data_dict = {
                u'user_id': user_id,
                u'result_code': int(result_code),
                u'result_text': result_text
            }

            return data_dict
        except Exception as e:
            return None

    
    def _make_logout_request(self, user_id, login_date, login_time):
        sysid = self._get_exat_sysid()

        ns = {
            'xmlns:SOAP-ENV': 'http://schemas.xmlsoap.org/soap/envelope/'
        }

        envelope = ET.Element('SOAP-ENV:Envelope', ns)
        header = ET.SubElement(envelope, 'SOAP-ENV:Header')
        body = ET.SubElement(envelope, 'SOAP-ENV:Body')
        security_param = ET.SubElement(body, 'Security_Param')
        data = ET.SubElement(security_param, 'Data')

        ET.SubElement(data, 'U_ID').text = user_id
        ET.SubElement(data, 'SYSID').text = sysid
        ET.SubElement(data, 'U_DateLogin').text = login_date
        ET.SubElement(data, 'U_TimeLogin').text = login_time

        sopa_request = ET.tostring(envelope).decode()

        return sopa_request


    def _parse_logout_response(self, soap_response):
        if soap_response is None:
            return None

        try:
            root = ET.fromstring(soap_response)

            # Find the relevant elements in the SOAP response and extract the required information
            data_element = root.find('.//EXAT_SecurityCenter/Data')
            result_code = data_element.findtext('ResultCode')
            result_text = data_element.findtext('ResultText')
            logout_date = data_element.findtext('U_DateLogout')
            logout_time = data_element.findtext('U_TimeLogout')

            # Create the data_dict using the extracted information
            data_dict = {
                u'result_code': int(result_code),
                u'result_text': result_text,
                u'logout_date': logout_date,
                u'logout_time': logout_time
            }

            return data_dict
        except Exception as e:
            return None
    

    def _make_password_encrypt_request(self, password):
        sysid = self._get_exat_sysid()

        ns = {
            'xmlns:SOAP-ENV': 'http://schemas.xmlsoap.org/soap/envelope/'
        }

        envelope = ET.Element('SOAP-ENV:Envelope', ns)
        header = ET.SubElement(envelope, 'SOAP-ENV:Header')
        body = ET.SubElement(envelope, 'SOAP-ENV:Body')
        security_param = ET.SubElement(body, 'Security_Param')
        data = ET.SubElement(security_param, 'Data')

        ET.SubElement(data, 'U_O_Pass').text = password

        sopa_request = ET.tostring(envelope).decode()

        return sopa_request
    

    def _parse_password_encrypt_response(self, soap_response):
        if soap_response is None:
            return None

        try:
            root = ET.fromstring(soap_response)

            # Find the relevant elements in the SOAP response and extract the required information
            data_element = root.find('.//EXAT_SecurityCenter/Data')
            result_code = data_element.findtext('ResultCode')
            result_text = data_element.findtext('ResultText')
            encrpty_password = data_element.findtext('U_N_Pass')

            # Create the data_dict using the extracted information
            data_dict = {
                u'result_code': int(result_code),
                u'result_text': result_text,
                u'encrpty_password': encrpty_password
            }

            return data_dict
        except Exception as e:
            return None


    def _make_get_user_info_request(self, user_id):
        sysid = self._get_exat_sysid()
        ip = self._get_exat_soap_ip()

        ns = {
            'xmlns:SOAP-ENV': 'http://schemas.xmlsoap.org/soap/envelope/'
        }

        envelope = ET.Element('SOAP-ENV:Envelope', ns)
        header = ET.SubElement(envelope, 'SOAP-ENV:Header')
        body = ET.SubElement(envelope, 'SOAP-ENV:Body')
        security_param = ET.SubElement(body, 'Security_Param')
        data = ET.SubElement(security_param, 'Data')

        ET.SubElement(data, 'U_ID').text = user_id

        sopa_request = ET.tostring(envelope).decode()

        return sopa_request


    def _parse_get_user_info_response(self, soap_response):
        if soap_response is None:
            return None

        try:
            root = ET.fromstring(soap_response)

            # Find the relevant elements in the SOAP response and extract the required information
            data_element = root.find('.//EXAT_SecurityCenter/Data')
            user_id = data_element.findtext('U_ID')
            prefix = data_element.findtext('U_Prefix')
            fname = data_element.findtext('U_Fname')
            lname = data_element.findtext('U_Lname')
            depart_code = data_element.findtext('U_DepartCode')
            depart_text = data_element.findtext('U_DepartText')
            position = data_element.findtext('U_Position')
            result_code = data_element.findtext('ResultCode')
            result_text = data_element.findtext('ResultText')
            login_date = data_element.findtext('U_DateLogin')
            login_time = data_element.findtext('U_TimeLogin')

            # Create the data_dict using the extracted information
            data_dict = {
                u'user_id': user_id,
                u'full_name': '{} {} {}'.format(prefix, fname, lname),
                u'department_code': depart_code,
                u'department_name': depart_text,
                u'position': position,
                u'result_code': int(result_code),
                u'result_text': result_text,
                u'login_date': login_date,
                u'login_time': login_time
            }

            return data_dict
        except Exception as e:
            return None