#-*- coding: utf-8 -*-
#
# COPYRIGHT FUJITSU SOCIAL SCIENCE LABORATORY LIMITED 2012
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without modification,
# are permitted provided that the following conditions are met:
#
# + Redistributions of source code must retain the above copyright notice, this list of conditions
# and the following disclaimer.
# + Redistributions in binary form must reproduce the above copyright notice, this list of conditions
# and the following disclaimer in the documentation and/or other materials provided with the distribution.
# + Neither the name of the FUJITSU SOCIAL SCIENCE LABORATORY LIMITED nor the names of its contributors
# may be used to endorse or promote products derived from this software without specific prior written
# permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND ANY EXPRESS OR
# IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND
# FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR
# CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
# DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
# DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY,
# WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN
# ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

import string
import httplib
import hashlib
from koala.settings import EUCA_HOST
# import json # require python 2.6
import logging
from logging import Logger

from os import path

u"""EucalyptusHttpAuthenticator.

EucalyptusHttpAuthenticator Authenticate using the HTTP server Eucalyptus front-end.
"""

class EucalyptusHttpAuthenticator(object):
    logger = None

    @staticmethod
    def set_logger(logger=None):
        if logger == None:
            raise ValueError('logger None')
        elif not isinstance(logger, Logger):
            raise TypeError('not logger instance')
        else:
            EucalyptusHttpAuthenticator.logger = logger

    def __set_logger(self):
        """
        logger setting
        """
        if EucalyptusHttpAuthenticator.logger == None:
            logger = logging.getLogger("eucalyptus_http")
            logger.setLevel(logging.DEBUG)
            #create console handler and set level to debug
            handler = logging.StreamHandler()
            handler.setLevel(logging.DEBUG)
            formatter = logging.Formatter(
                "%(asctime)s - %(name)s - %(levelname)s - %(message)s")
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            self.logger = logger
        else:
            self.logger = EucalyptusHttpAuthenticator.logger

    DEFAULT_LOGGER_CONFIG = path.dirname( path.abspath( __file__ ) )+ '/log.conf'
    EUCALYPTUS_HTTP_AUTH_METHOD = 'POST'
    EUCALYPTUS_HTTP_POST_REQUEST_URI = '/backend'
    #EUCALYPTUS_HTTP_POST_REQUEST_URI = '/EucalyptusWebBackend'
    #EUCALYPTUS_GWT_HTTP_POST_CONTENT = string.Template(
    #    '5|0|7|$schema://$host:$port/|2|edu.ucsb.eucalyptus.admin.client.EucalyptusWebBackend|getNewSessionID|java.lang.String/|$user_id|$md5_password|1|2|3|4|2|5|5|6|7|'
    #)

    EUCALYPTUS_GWT_HTTP_POST_CONTENT = string.Template(
    '7|0|8|$schema://$host:$port/|$request_id|com.eucalyptus.webui.client.service.EucalyptusService|login|java.lang.String/2004016611|$account_id|$user_id|$password|1|2|3|4|3|5|5|5|6|7|8|')

    HTTP_HEADER_CONTET_TYPE ='Content-Type'
    HTTP_HEADER_GWT_PERMUTATION='X-GWT-Permutation'

    GWT_CONTENT_TYPE='text/x-gwt-rpc; charset=utf-8'
    EUCALYPTUS_GWT_AUTH_OK = '//OK'
    EUCALYPTUS_GWT_AUTH_NG = '//EX'
    schema = None
    host = None
    port = None
    verify = None   # not use
    gwt_permutation = None
    request_id = None

    """
    A Eucalyptus Frontend Information verify
    """
    @staticmethod
    def __verify_eucalyptus_frontend(schema='https',host=EUCA_HOST,port=8443,verify=False):
        if schema == None or host==None or port==None or verify == None:
            raise ValueError('arguments not allowed None value.')
        if schema != 'https' and schema != 'http':
            raise ValueError('suport protocls http or https.')
        port = int(port)
        if  port < 0 or 65535 < port:
            raise ValueError('port range 0-65535.port :' + str(port))
        verify = bool(verify)
        if not isinstance(verify, bool):
            raise TypeError('argument verify Type must be bool.')
        return


    """
    A Eucalyptus Frontend Login pages HTTP-POST Object
    """
    def __init__(self,schema='https',host=EUCA_HOST,port=8443,verify=False):
        """
        Initialize EucalyptusHttpAuthenticate object.
        :schema:
            http or https
        :host:
            Eucalyptus Frontend worked Host.
            DNS name or IP Address (tested IPv4)
        :port:
            Frontend service port
        :verify:
            allowed self signed certificate
        """
        self.__set_logger()
        EucalyptusHttpAuthenticator.__verify_eucalyptus_frontend(schema,host,port,verify)
        self.schema = schema
        self.host = host
        self.port = port
        self.verify = verify
        self.logger.debug('initialize: ' + str(self))
        return

    @staticmethod
    def global_setting(schema='https',host=EUCA_HOST,port=8443,verify=False,gwt_permutation='',request_id=''):
        """
        Initialize EucalyptusHttpAuthenticate class.
        :schema:
            http or https
        :host:
            Eucalyptus Frontend worked Host.
            DNS name or IP Address (tested IPv4)
        :port:
            Frontend service port
        :verify:
            allowed self signed certificate
        :gwt_permutation:
            X-GWT-Permutation
        """
        EucalyptusHttpAuthenticator.__verify_eucalyptus_frontend(
            schema,host,port,verify
        )
        EucalyptusHttpAuthenticator.schema = schema
        EucalyptusHttpAuthenticator.host = host
        EucalyptusHttpAuthenticator.port = port
        EucalyptusHttpAuthenticator.verify = verify
        EucalyptusHttpAuthenticator.gwt_permutation = gwt_permutation
        EucalyptusHttpAuthenticator.request_id = request_id

        return

    @staticmethod
    def get_http_post_content(
        schema='https',host=EUCA_HOST,port=8443,account_id='eucalyptus', user_id='admin',password='password',request_id='id'):
        return EucalyptusHttpAuthenticator.EUCALYPTUS_GWT_HTTP_POST_CONTENT.substitute(
            {'schema':schema,'host':host,'port':port,'account_id':account_id,'user_id':user_id,'password':password,'request_id':request_id}
        )

    @staticmethod
    def __get_instance():
        return EucalyptusHttpAuthenticator(
            EucalyptusHttpAuthenticator.schema,
            EucalyptusHttpAuthenticator.host,
            EucalyptusHttpAuthenticator.port,
            EucalyptusHttpAuthenticator.verify
    )

    @staticmethod
    def get_session_id_by_global_setting(account_id=None, user_id=None,password=None):
        return EucalyptusHttpAuthenticator.__get_instance().get_session_id(account_id,user_id,password)

    def get_session_id(self,account_id=None,user_id=None,password=None):
        """
        HTTP POST (GWT Conetnt) execute
        """
        if account_id == None and user_id == None and password == None:
            raise ValueError('account_id or user_id or user_password  was None.')
        http_client = None
        try:
            if self.schema == 'http':
                http_client = httplib.HTTPConnection(self.host,self.port)
            elif self.schema == 'https':
                # FIXME python httplib certificate not verify!
                http_client = httplib.HTTPSConnection(self.host,self.port)
            else:
                raise ValueError('Invalid schema : ' + self.schema)
        except:
            raise
        if http_client == None:
            raise RuntimeError()
        response =  None

        post_content = EucalyptusHttpAuthenticator.get_http_post_content(
            self.schema,
            self.host,
            self.port,
            account_id,
            user_id,
            password,
            self.request_id
        )

        #self.logger.debug('post_content='+ post_content )

        authorized = False

        try:
            headers={
                EucalyptusHttpAuthenticator.HTTP_HEADER_CONTET_TYPE : EucalyptusHttpAuthenticator.GWT_CONTENT_TYPE,
                 EucalyptusHttpAuthenticator.HTTP_HEADER_GWT_PERMUTATION : EucalyptusHttpAuthenticator.gwt_permutation
            }
            http_client.request(
                EucalyptusHttpAuthenticator.EUCALYPTUS_HTTP_AUTH_METHOD,
                EucalyptusHttpAuthenticator.EUCALYPTUS_HTTP_POST_REQUEST_URI,
                post_content,
                headers
            )

            response = http_client.getresponse()
            if response.status != httplib.OK:
                self.logger.debug(
                    'bad status : ' + str(response.status) +
                    'error reason : ' + response.reason
                )
                return False
            result = response.read()
            if result.startswith(EucalyptusHttpAuthenticator.EUCALYPTUS_GWT_AUTH_OK):
                self.logger.debug ('authenticate succeed user_id: ' + user_id + ' . result :' + result)
                authorized = True
                # TODO json result
#               result_json = json.loads(result[len(EucalyptusHttpAuthenticator.EUCALYPTUS_GWT_AUTH_OK):])
            else:
                self.logger.debug ('authenticate failed user_id: ' + user_id + ' . result :' + result)
                # TODO json result (to Exception)
#               if result.startswith(EucalyptusHttpAuthenticator.EUCALYPTUS_GWT_AUTH_NG):
#                   result_json = json.loads(result[len(EucalyptusHttpAuthenticator.EUCALYPTUS_GWT_AUTH_NG):])
        except Exception ,e:
            self.logger.error('get_session_id exceptin happened : ' + str(e))
            raise e
        finally:
            try:
                if response != None and not (response.isclosed()):
                    response.close()
                response = None
                if http_client != None:
                    http_client.close()
            except:
                self.logger.warning('get_session_id http_client#close happened : ' + str(e))
            finally:
                http_client = None
        return authorized

    @staticmethod
    def get_digest_message(target=None):
        """
        GWT using password hash algorism used md5
        """
        if target == None:
            raise ValueError('md5 update target not allow None.')
        message_digest= hashlib.md5()
        message_digest.update(target)
        return message_digest.hexdigest()

    PRETTY_PRINT = string.Template(
        'auth(server : $schema://$host:$port ,self-signed : $is_self_signed)'
    )

    def __repr__(self):
        is_self_signed = 'allow'
        if self.verify:
            is_self_signed = 'deny'
        return EucalyptusHttpAuthenticator.PRETTY_PRINT.substitute(
            {
             'schema':self.schema,
             'host':self.host,
             'port':self.port,
             'is_self_signed':is_self_signed
            }
        )


