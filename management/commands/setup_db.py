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

from koala.eucalyptus.models import Image,User,VMType,Template,Charge
from django.core.management.base import BaseCommand
from koala.management.commands.batch_common import BatchCommon
from koala.eucalyptus.euca_access import GetEucalyptusInfo
import logging, csv

class Command(BaseCommand):

	help = u'koalaのDBデータの初期登録バッチです'

	#カスタムログ
	logger = logging.getLogger('koalasetuplog')

	#Eucalyptus基盤へのアクセサを生成する
	get_euca_info=GetEucalyptusInfo()

	images = get_euca_info.get_image()
	vmtype_list = get_euca_info.get_vmtypes(db_user=None)

	def handle(self, *args, **options):

		# ------------------------------------------------------
		#                      主処理
		# ------------------------------------------------------

		self.logger.info('-----初期自動セットアップの開始-----')

		#batch = BatchCommon()
		#ユーザの登録
		#new_user_list = batch.registUser()
		#batch.registUser()

		#イメージの登録
		#new_image_list = self.registImage()

		#テンプレートの登録
		#self.registTemplate(new_user_list, new_image_list)

		#VMTypeの登録
		self.registVMType()

		self.logger.info('-----初期自動セットアップ完了-----')


	#Koala内部DBにイメージを登録するメソッド
	def registImage(self):

		self.logger.info('-----イメージの登録開始-----')

		new_image_list = []

		for i in self.images:

			new_image = Image()

			location = i.location.encode('utf-8')
			image_str=location.split('/')

			new_image.image_id = i.id

			if i.root_device_type == 'ebs':
				#EBSブートの登録処理
				try:
					ebs_owner = User.objects.get(account_number=i.ownerId, user_id='admin')
					new_image.name = ebs_owner.account_id.encode('utf-8')
					new_image.description = new_image.name +'のイメージです。'

				except User.DoesNotExist, ex:
					self.logger.error('ebs bootイメージ[%s]の登録失敗' % new_image.image_id.encode('utf-8'))
					self.logger.error(ex)

			else:
				new_image.name = image_str[0]
				new_image.description = image_str[0]+'のイメージです。'

			try:
				Image.objects.get(image_id=new_image.image_id)
				self.logger.info('イメージ[%s]の登録スキップ' % new_image.image_id.encode('utf-8'))
			except Image.DoesNotExist:
				new_image.save()
				self.logger.info('イメージ[%s]の登録完了' % new_image.image_id.encode('utf-8'))
				new_image_list.append(new_image)

			except Exception, ex:

				self.logger.warn('イメージ[%s]の登録失敗' % new_image.image_id.encode('utf-8'))
				self.logger.error(ex)

		self.logger.info('-----イメージの登録完了-----')
		return new_image_list


	#Koala内部DBにテンプレートを登録するメソッド
	def registTemplate(self, new_user_list, new_image_list):

		#管理者ユーザ、アカウントの定義
		admin_user = 'admin'
		admin_account = 'eucalyptus'

		csvTemplatefile = '../koala/management/commands/template.csv'
		readerTemplate = csv.reader(file(csvTemplatefile, 'r'))
		csvTemplate = self.createCSVTemplate(readerTemplate)

		images = self.images

		self.logger.info('-----初期テンプレートの作成開始-----')

		for image in new_image_list:
			machine_flag = False
			new_template = Template()
			new_template.name = image.name.encode('utf-8')+'テンプレート'
			new_template.description = image.name.encode('utf-8')+'のテンプレートです。'
			new_template.image_id = image.image_id
			new_template.vmtype = 'm1.small'

			for i in images:
				if i.id == image.image_id:
					if i.type == "machine":
						machine_flag = True

						for u in new_user_list:
							#admin@eucalyptusが存在することを確認
							if u.account_number == i.ownerId and u.user_id == admin_user:
								new_template.user_id = admin_user
								new_template.account_id = admin_account

								#イメージの種別を判定する
								new_template.kind = 1 if u.admin else 0
								break

						csv_template = self.getCSVTemplate(i.location.encode('utf-8'),csvTemplate)
						if csv_template != None:
							new_template.name=csv_template.name.encode('utf-8')
							new_template.description=csv_template.description.encode('utf-8')
							new_template.vmtype=csv_template.vmType.encode('utf-8')
							new_template.count=csv_template.count.encode('utf-8')
						break

			if machine_flag:
				try:
					new_template.save()
					self.logger.info('テンプレート[%s]の登録完了' % new_template.name)

				except  Exception, ex:
					self.logger.warn('テンプレート[%s]の登録失敗' % new_template.name)
					self.logger.error(ex)

		self.logger.info('-----初期テンプレートの作成完了-----')


	#Koala内部DBにVMTypeを登録するメソッド
	def registVMType(self):

		self.logger.info('-----VMTypeの登録-----')

		vmtype_list = self.vmtype_list

		for i in range(0, len(vmtype_list)):
			new_vmtype = VMType()
			new_vmtype.vmtype = vmtype_list[i].vmtype
			new_vmtype.name = vmtype_list[i].vmtype
			new_vmtype.cpu = vmtype_list[i].cpu
			new_vmtype.mem = vmtype_list[i].mem
			new_vmtype.hdd = vmtype_list[i].disk
			new_vmtype.order = i

			try:
				new_vmtype.save()
				self.logger.info('VMType[%s]の登録完了 '% vmtype_list[i].vmtype)
			except  Exception, ex:
				self.logger.info('MType[%s]の登録失敗' % vmtype_list[i].vmtype)
				self.logger.error(ex)

		self.logger.info('-----VMTypeの登録完了-----')


	def createCSVTemplate(self, reader=None):
		TemplateCSV = []

		if reader == None:
			return []

		for row in reader:

			template = CSVTemplate()

			if row[0][0] == '#':
				continue

			template.location=row[0].decode('utf_8')
			template.name=row[1].decode('utf_8')
			template.description=row[2].decode('utf_8')
			template.vmType=row[3].decode('utf_8')
			template.count=row[4].decode('utf_8')

			TemplateCSV.append(template)

		return TemplateCSV


	def getCSVTemplate(self, location="", csvTemplate=[]):

		for csv in csvTemplate:
			if location == csv.location:
				return csv

		return None


class CSVTemplate(object):

	def __init__(self):
		self.location=""
		self.name=""
		self.description=""
		self.vmType="m1.small"
		self.count=1