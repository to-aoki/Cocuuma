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

from django.db import models
from django import forms
from django.core.files import File
import base64


class MachineGroup(models.Model):
	name = models.CharField(u'サーバグループ名',max_length=256)
	description = models.CharField(u'説明',max_length=256,null=True,blank=True)
	account_id = models.CharField(u'アカウントID',max_length=20)
	user_id = models.CharField(u'ユーザーID',max_length=20)

	def __unicode__(self):
		return u'%d %s' % (self.id, self.name)

	class Meta:
		db_table = 'machinegroup'

class Machine(models.Model):
	group = models.ForeignKey(MachineGroup, verbose_name=u'サーバグループID')
	name = models.CharField(u'サーバ名',max_length=256)
	instance_id = models.CharField(u'インスタンスID',max_length=20,null=True,blank=True)
	image_id = models.CharField(u'イメージID',max_length=20)
	vmtype = models.CharField(u'VMType',max_length=10)
	ip = models.IPAddressField(u'IPアドレス',max_length=15,null=True,blank=True)
	keypair =  models.CharField(u'キーペア名',max_length=20,default='mykey')
	security_group =  models.CharField(u'セキュリティグループ名',max_length=20,default='default')
	avaulability_zone = models.CharField(u'AvaulabilityZone',max_length=20,null=True,blank=True)
	user_data = models.CharField(u'ユーザーデータ',max_length=1024,null=True,blank=True)
	template_id = models.IntegerField(u'テンプレートID')
	order = models.IntegerField(u'表示順',default=0)

	def __unicode__(self):
		return u'%d %s' % (self.id, self.name)

	class Meta:
		db_table = 'machine'

class User(models.Model):
	account_id = models.CharField(u'アカウント名',max_length=20)
	account_number = models.CharField(u'アカウントID',max_length=20)
	user_id = models.CharField(u'ユーザー名',max_length=32)
	name = models.CharField(u'ユーザー＠アカウント',max_length=256)
	user_number = models.CharField(u'ユーザーID',max_length=20)
	accesskey = models.CharField(u'アクセスキー',max_length=256)
	secretkey = models.CharField(u'シークレットキー',max_length=256)
	admin = models.BooleanField(u'管理者権限',default=False)
	permission = models.CharField(u'表示権限',max_length=20,default='10010000')
	maxvm = models.IntegerField(u'仮想マシン上限',default=10)
	maxvol = models.IntegerField(u'ボリューム容量上限',default=50)
	maxip = models.IntegerField(u'IPアドレス上限',default=5)
	created_date = models.DateTimeField(auto_now_add=True)
	updated_date = models.DateTimeField(auto_now=True)
	enabled_stat = models.BooleanField(u'有効',default=False)
	user_desc = models.CharField(u'説明',max_length=256)
	user_path =  models.CharField(u'パス',max_length=256)


	def __unicode__(self):
		return u'%s@%s' % (self.user_id, self.account_id)

	class Meta:
		db_table = 'user'
		unique_together = ('account_id', 'user_id')


class Group(models.Model):
	group_id = models.CharField(u'グループID',max_length=55)
	group_name = models.CharField(u'グループ名',max_length=256)
	account_id = models.CharField(u'アカウントID',max_length=55)
	group_desc = models.CharField(u'説明',max_length=256,null=True,blank=True)
	group_path =  models.CharField(u'パス',max_length=256)
	account_name = models.CharField(u'アカウント名',max_length=256)
	group_pol = models.CharField(u'ポリシー情報',max_length=256,null=True,blank=True)

	def __unicode__(self):
		return self.group_id

	class Meta:
		db_table = 'group'


class Template(models.Model):
	name = models.CharField(u'テンプレート名',max_length=256)
	account_id = models.CharField(u'アカウントID',max_length=20)
	user_id = models.CharField(u'ユーザーID',max_length=20)
	description = models.CharField(u'説明',max_length=256,null=True,blank=True)
	image_id = models.CharField(u'イメージID',max_length=20)
	count = models.IntegerField(u'イメージ数',default=1)
	vmtype = models.CharField(u'VMType',max_length=20)
	kind = models.IntegerField(u'種別',blank=0)

	def __unicode__(self):
		return u'%d %s' % (self.id, self.name)

	class Meta:
		db_table = 'template'

class Image(models.Model):
	image_id = models.CharField(u'イメージID',max_length=20,primary_key=True)
	name = models.CharField(u'イメージ名',max_length=256)
	description = models.CharField(u'説明',max_length=256,null=True,blank=True)

	def __unicode__(self):
		return self.image_id

	class Meta:
		db_table = 'image'

class VMType(models.Model):
	vmtype = models.CharField(u'VMTYPE',max_length=20,primary_key=True)
	name = models.CharField(u'リソース名',max_length=256)
	cpu = models.IntegerField(u'CPUコア数',default=0)
	mem = models.IntegerField(u'メモリ[MB]',default=0)
	hdd = models.IntegerField(u'HDD[GB]',default=0)
	order = models.IntegerField(u'表示順',default=0)

	def __unicode__(self):
		return self.vmtype

	class Meta:
		db_table = 'vmtype'
		ordering = ["order"]

	def _get_full_name(self):
		"Returns the VMType's full name."
		return u"%s　CPU：%d[コア]  メモリ：%d[MB]  (instance-storeタイプのOSイメージ最大サイズ：%d[GB]）"  % (self.name, self.cpu, self.mem, self.hdd)
	full_name = property(_get_full_name)

class Volume(models.Model):
	volume_id = models.CharField(u'ボリュームID',max_length=20,primary_key=True)
	machine = models.ForeignKey(Machine, verbose_name=u'仮想サーバID',null=True,blank=True)
	account_id = models.CharField(u'アカウントID',max_length=20)
	user_id = models.CharField(u'ユーザーID',max_length=20)
	name = models.CharField(u'ボリューム名',max_length=256)
	description = models.CharField(u'説明',max_length=256,null=True,blank=True)

	def __unicode__(self):
		return self.volume_id

	class Meta:
		db_table = 'volume'
		ordering = ['volume_id']


class Base64Field(models.Field):
	description = 'Base64 Field'

	def get_internal_type(self):
		return "TextField"

	def clean(self, value, model_instance):
		if isinstance(value, File):
			model_instance.name = value.name
			return base64.b64encode(value.read())
		return value

	def formfield(self, **kwargs):
		defaults = {'form_class': forms.FileField}
		if 'initial' in kwargs:
			defaults['required'] = False
		defaults.update(kwargs)
		return super(Base64Field, self).formfield(**defaults)

class Keypair(models.Model):
	account_id = models.CharField(u'アカウントID',max_length=20)
	user_id = models.CharField(u'ユーザーID',max_length=20)
	name = models.CharField(u'接続鍵名',max_length=256)
	data = Base64Field(u'鍵ファイル',null=True,blank=True)

	def __unicode__(self):
		return u'%s@%s %s' % (self.user_id, self.account_id, self.name)

	class Meta:
		db_table = 'keypair'
		unique_together = ('account_id', 'user_id', 'name')
		ordering = ['account_id', 'user_id', 'name']

class Charge(models.Model):
	charge = models.CharField(u'課金名',max_length=128,primary_key=True,default="デフォルト時間課金")
	boot = models.FloatField(u'仮想マシン配備ポイント(/回)',default=10.0)
	cpu = models.FloatField(u'CPUコアポイント(/core*時間)',default=2.0)
	mem = models.FloatField(u'メモリポイント(/GB*時間)',default=1.0)
	disk = models.FloatField(u'ディスクIOポイント(/GB)',default=0.05)
	net = models.FloatField(u'ネットワーク転送ポイント(/GB)',default=0.05)
	ebs = models.FloatField(u'EBSボリューム利用(/GB*時間)',default=0.2)
	snapshot = models.FloatField(u'スナップショット利用(/GB*時間)',default=0.2)
	walrus = models.FloatField(u'Walrus利用(/GB*時間)',default=0.1)

	def __unicode__(self):
		return self.charge

	class Meta:
		db_table = 'charge'

class Host(models.Model):
	hostname = models.CharField(u'ホスト名',max_length=128,primary_key=True,default="clc00")
	monitored_hostname = models.CharField(u'監視ホスト名',max_length=128,default="clc00")
	registered_ip = models.CharField(u'登録IPアドレス',max_length=128,default="0.0.0.0")
	monitored_ip = models.CharField(u'監視IPアドレス',max_length=128,default="0.0.0.0")

	def __unicode__(self):
		return self.hostname

	class Meta:
		db_table = 'host'


class Policyset(models.Model):
	psetname = models.CharField(u'権限セット名',max_length=256)
	pname = models.CharField(u'ポリシー名',max_length=256)
	pcontent = models.CharField(u'ポリシー文書',max_length=500,null=True,blank=True)
	psetdesc = models.CharField(u'ポリシー説明',max_length=256,null=True,blank=True)

	def __unicode__(self):
		return self.pname

	class Meta:
		db_table = 'policyset'

