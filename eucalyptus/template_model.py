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

class Template_Model(object):

	def __init__(self,db_template_object=None,user_object=None,image_object=None,vmtype_object=None):
		self.db_template = db_template_object
		self.userdata = user_object
		self.imagedata = image_object
		self.vmtypedata = vmtype_object

	@property
	def id(self):
		return str(self.db_template.id)

	@id.getter
	def id(self):
		return str(self.db_template.id)

	@property
	def name(self):
		return self.db_template.name

	@name.setter
	def name(self,value):
		self.db_template.name = value
		self.save()

	@name.getter
	def name(self):
		return self.db_template.name

	@property
	def user(self):
		return self.userdata

	@user.setter
	def user(self,value):
		self.userdata = value
		self.db_template.user_id=self.userdata.id
		self.save()

	@user.getter
	def user(self):
		return self.userdata

	@property
	def description(self):
		return self.db_template.description

	@description.setter
	def description(self,value):
		self.db_template.description = value;
		self.save()

	@description.getter
	def description(self):
		return self.db_template.description

	@property
	def image(self):
		return self.imagedata

	@image.setter
	def image(self,value):
		self.imagedata = value
		self.db_template.image_id = self.imagedata.id
		self.save()

	@image.getter
	def image(self):
		return self.imagedata

	@property
	def count(self):
		return self.db_template.count

	@count.setter
	def count(self,value):
		self.db_template.count = value

	@count.getter
	def count(self):
		return self.db_template.count

	@property
	def vmtype(self):
		return self.vmtypedata

	@vmtype.setter
	def vmtype(self,value):
		self.vmtypedata = value
		self.db_template.vmtype = self.vmtypedata.vmtype
		self.save()

	@vmtype.getter
	def vmtype(self):
		return self.vmtypedata

	@property
	def kind(self):
		return self.db_template.kind

	@kind.setter
	def kind(self,value):
		if value <= 1:
			self.db_template.kind = value
			self.save()

	@kind.getter
	def kind(self):
		return self.db_template.kind

	#DBの情報を更新する
	def save(self):
		self.db_template.save()
		self.user.save()
		self.imagedata.save()
		self.vmtypedata.save()

	#DBのテンプレート情報を削除する
	def delete(self):
		self.db_template.delete()

