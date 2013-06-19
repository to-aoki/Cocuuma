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

u"""EucalyptusAuthenticator Authenticator.

EucalyptusAuthenticator Authenticate using the HTTP server Eucalyptus front-end.
"""

class EucalyptusAuthenticator(object):
    EUCALYPTUS_HTTP_AUTH_METHOD = 'POST'
    EUCALYPTUS_HTTP_POST_REQUEST_URI = '/EucalyptusWebBackend'
    EUCALYPTUS_GWT_HTTP_POST_CONTENT = string.Template(
        '5|0|7|$schema://$host:$port/|2|edu.ucsb.eucalyptus.admin.client.EucalyptusWebBackend|getNewSessionID|java.lang.String/|$user_id|$md5_password|1|2|3|4|2|5|5|6|7|'
    )
    HTTP_HEADER_CONTET_TYPE ='Content-Type'
    GWT_CONTENT_TYPE='text/x-gwt-rpc; charset=utf-8'
    EUCALYPTUS_GWT_AUTH_OK = '//OK'
    EUCALYPTUS_GWT_AUTH_NG = '//EX'
    schema = None
    host = None
    port = None
    verify = None   # not use
    """
    A Eucalyptus Frontend Information verify
    """
    @staticmethod
    def __verify_eucalyptus_frontend(schema='http',host=EUCA_HOST,port=80,verify=False):
        if schema == None or host==None or port==None or verify == None:
            print schema

            raise ValueError('arguments not allowed None value.')
        if schema != 'https' and schema != 'http':
            raise ValueError('suport protocls http or https.')
        if not (port <= 0 or port <= 65535):
            raise ValueError('port range 0-65535')
        if not isinstance(verify, bool):
            raise TypeError('argument verify Type must be bool.')
        return

    """
    A Eucalyptus Frontend Login pages HTTP-POST Object
    """
    def __init__(self,schema='http',host=EUCA_HOST,port=80,verify=False):
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
        EucalyptusAuthenticator.__verify_eucalyptus_frontend(schema,host,port,verify)
        self.schema = schema
        self.host = host
        self.port = port
        self.verify = verify
        return

    @staticmethod
    def global_setting(schema='http',host=EUCA_HOST,port=80,verify=False):
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
        """
        EucalyptusAuthenticator.__verify_eucalyptus_frontend(schema,host,port,verify)
        EucalyptusAuthenticator.schema = schema
        EucalyptusAuthenticator.host = host
        EucalyptusAuthenticator.port = port
        EucalyptusAuthenticator.verify = verify
        return

    @staticmethod
    def get_http_post_content(schema='http',host=EUCA_HOST,port=80,user_id='test',md5_password='md5password'):
        return EucalyptusAuthenticator.EUCALYPTUS_GWT_HTTP_POST_CONTENT.substitute({'schema':schema,'host':host,'port':port,'user_id':user_id,'md5_password':md5_password})

    @staticmethod
    def __get_global_instance():
        return EucalyptusAuthenticator(EucalyptusAuthenticator.schema,EucalyptusAuthenticator.host,EucalyptusAuthenticator.port,EucalyptusAuthenticator.verify)

    @staticmethod
    def get_session_id_by_global_setting(user=None,password=None):
        return EucalyptusAuthenticator.__get_global_instance().get_session_id(user,password)

    def get_session_id(self,user_id=None,password=None):
        """
        HTTP POST (GWT Conetnt) execute
        """
        if user_id == None and password == None:
            raise ValueError('user_id or user_password was None.')
        post_content = EucalyptusAuthenticator.get_http_post_content(
            self.schema,
            self.host,
            self.port,
            user_id,
            EucalyptusAuthenticator.get_digest_message(password)
        )
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
            raise RutimeError()
        response =  None
        authorized = False
        try:
            headers={
                EucalyptusAuthenticator.HTTP_HEADER_CONTET_TYPE : EucalyptusAuthenticator.GWT_CONTENT_TYPE
            }
            http_client.request(
                EucalyptusAuthenticator.EUCALYPTUS_HTTP_AUTH_METHOD,
                EucalyptusAuthenticator.EUCALYPTUS_HTTP_POST_REQUEST_URI,
                post_content,
                headers
            )
            response = http_client.getresponse()
            if response.status != httplib.OK:
                print 'bad status : ' + response.status
                print 'error reason : ' + response.reason
                return False
            result = response.read()
            print result
            if result.startswith(EucalyptusAuthenticator.EUCALYPTUS_GWT_AUTH_OK):
                authorized = True
                # TODO json result
#               result_json = json.loads(result[len(EucalyptusAuthenticator.EUCALYPTUS_GWT_AUTH_OK):])
#               print result_json[1] # eucalyptus session-id
            else:
                print 'authenticate failed user_id: ' + user_id + ' . result :' + result
                # TODO json result (to Exception)
#               if result.startswith(EucalyptusAuthenticator.EUCALYPTUS_GWT_AUTH_NG):
#                   result_json = json.loads(result[len(EucalyptusAuthenticator.EUCALYPTUS_GWT_AUTH_NG):])
#                   print result_json[2][1] # reason
        except Exception ,e:
            print 'error!' + e
            raise e
        finally:
            try:
                if response != None and not (response.isclosed()):
                    response.close()
                response = None
                if http_client != None:
                    http_client.close()
            except:
                print 'connection closing error'
        return authorized

    @staticmethod
    def get_digest_message(target=None):
        """
        GWT using password hash algorism used md5
        """
        if target == None:
            raise ValueError('md5 update target not allow None.')
        hash = hashlib.md5()
        hash.update(target)
        return hash.hexdigest()

