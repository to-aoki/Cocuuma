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

class User_Model(object):

    def __init__(self,db_user_object):
        #ユーザのDBオブジェクト
        self.db_user = db_user_object;
        #botoAPI呼び出し最終時刻
        self.last_cmd = 0.0

    @property
    def account_id(self):
        return self.db_user.account_id

    @property
    def account_number(self):
        return self.db_user.account_number

    @property
    def id(self):
        return self.db_user.user_id

    @property
    def name(self):
        return self.db_user.name

    @name.setter
    def name(self,value):
        self.db_user.name = value
        self.save()

    @property
    def accesskey(self):
        return self.db_user.accesskey

    @property
    def secretkey(self):
        return self.db_user.secretkey

    @property
    def admin(self):
        return self.db_user.admin

    @admin.setter
    def admin(self,value):
        self.db_user.admin = value
        self.save()

    @property
    def permission(self):
        return self.db_user.permission

    @permission.setter
    def permission(self,value):
        self.db_user.permission = value
        self.save()

    @property
    def resource_admin(self):
        try:
            if self.db_user.user_id == 'admin' and self.db_user.account_id == 'eucalyptus':
                return True
            else:
                return False
        except:
            return False

    @property
    def imagepermission(self):
        try:
            if self.db_user.permission[1] == '0':
                return False
            else:
                return True
        except:
            return False

    @property
    def templatepermission(self):
        try:
            if self.db_user.permission[2] == '0':
                return False
            else:
                return True
        except:
            return False

    @property
    def machinepermission(self):
        try:
            if self.db_user.permission[3] == '0':
                return False
            else:
                return True
        except:
            return False

    @property
    def addresspermission(self):
        try:
            if self.db_user.permission[4] == '0':
                return False
            else:
                return True
        except:
            return False

    @property
    def volumepermission(self):
        try:
            if self.db_user.permission[5] == '0':
                return False
            else:
                return True
        except:
            return False

    @property
    def keypairpermission(self):
        try:
            if self.db_user.permission[6] == '0':
                return False
            else:
                return True
        except:
            return False

    @property
    def securitygrouppermission(self):
        try:
            if self.db_user.permission[7] == '0':
                return False
            else:
                return True
        except:
            return False

    #DBのユーザ情報を更新する
    def save(self):
        self.db_user.save()

    #DBのユーザ情報を削除する
    def delete(self):
        self.db_user.delete()
