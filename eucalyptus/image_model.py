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

class Image_Model(object):

    def __init__(self,db_image_object=None,euca_image_object=None):

        #イメージのDBオブジェクト
        self.db_image = db_image_object;
        #eucalyptusから取得されたイメージオブジェクト
        self.euca_image = euca_image_object;
        #ユーザモデル
        self.image_snapshot = None

    @property
    def id(self):
        return self.db_image.image_id

    @id.getter
    def id(self):
        return self.db_image.image_id

    @property
    def name(self):
        return self.db_image.name

    @name.setter
    def name(self,value):
        self.db_image.name = value
        self.save()

    @name.getter
    def name(self):
        return self.db_image.name

    @property
    def description(self):
        return self.db_image.description

    @description.setter
    def description(self,value):
        self.db_image.description = value
        self.save()

    @description.getter
    def description(self):
        return self.db_image.description

    @property
    def location(self):
        return self.euca_image.location

    @location.getter
    def location(self):
        return self.euca_image.location

    @property
    def state(self):
        return self.euca_image.state

    @state.getter
    def state(self):
        return self.euca_image.state

    @property
    def owner(self):
        return self.euca_image.ownerId

    @owner.getter
    def owner(self):
        return self.euca_image.ownerId

    @property
    def ownername(self):
        return self.euca_image.ownerId
        #return self.owner_name

    @ownername.getter
    def ownername(self):
        return self.euca_image.ownerId
        #return self.owner_name

    @property
    def account_id(self):
        return self.euca_image.ownerId
        #return self.account_number

    @account_id.getter
    def account_id(self):
        return self.euca_image.ownerId
        #return self.account_number

    @property
    def is_public(self):
        if self.euca_image.is_public == True:
            return 'public'
        else:
            return 'private'

    @is_public.getter
    def is_public(self):
        if self.euca_image.is_public == True:
            return 'public'
        else:
            return 'private'

    @property
    def architecture(self):
        return self.euca_image.architecture

    @architecture.getter
    def architecture(self):
        return self.euca_image.architecture

    @property
    def platform(self):
        if self.euca_image.platform == None:
            return ""
        else:
            return self.euca_image.platform

    @platform.getter
    def platform(self):
        if self.euca_image.platform == None:
            return ""
        else:
            return self.euca_image.platform

    @property
    def root_device_type(self):
        return self.euca_image.root_device_type

    @root_device_type.getter
    def root_device_type(self):
        return self.euca_image.root_device_type

    @property
    def type(self):
        return self.euca_image.type

    @type.getter
    def type(self):
        return self.euca_image.type

    #DBのイメージ情報を更新する
    def save(self):
        self.db_image.save()

    #DBのイメージ情報を削除する
    def delete(self):
        self.db_image.delete()

class Image_Snapshot(object):

    def __init__(self):
        self.image_id = None
        self.snapshot_id = None

