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

from django import forms
from euca_common import CustomFilePathField

import euca_common

import re

class ImageModForm(forms.Form):
	image_name = forms.CharField(max_length=256,widget=forms.TextInput(attrs={'class':'text'}),error_messages={'required': u'イメージ名を入力してください。','max_length': u'256文字以下で入力してください。'})
	image_description = forms.CharField(required=False,max_length=256,widget=forms.TextInput(attrs={'class':'text'}),error_messages={'max_length': u'256文字以下で入力してください。'})

	# フィールドの日本語名辞書
	nameDic = {"image_name":u"OSイメージ名", "image_description":u"説明"}

	def is_valid(self):
		if not self.errors:
			return True

		#エラーメッセージのフィールド名を日本語に置換
		for name in self.errors.keys():
			msgs = self.errors.pop(name)
			displayName = self.nameDic[name]
			error_list = forms.util.ErrorList()
			for msg in msgs:
				error_list.append( u"%s： %s" % (displayName, msg) )
			self.errors[displayName] = error_list

		return False

class ImageCreateStep1Form(forms.Form):

	#"""半角英数字、半角ハイフンアンダースコア、.のみ有効"""
	USERID_REGEX = re.compile(r"^[\.\w-]+$")

	image_name = forms.CharField(max_length=256,widget=forms.TextInput(attrs={'class':'text'}),error_messages={'required': u'イメージ名を入力してください。','max_length': u'256文字以下で入力してください。'})
	image_description = forms.CharField(required=False,max_length=256,widget=forms.TextInput(attrs={'class':'text'}),error_messages={'max_length': u'256文字以下で入力してください。'})
	bucket_name = forms.RegexField(max_length=256,
								regex=USERID_REGEX,widget=forms.TextInput(attrs={'class':'text'}),
								error_messages={'required': u'バケット名を入力してください。',
											'max_length': u'256文字以下で入力してください。','invalid': u'「半角英数字、半角ハイフンアンダースコア、半角.」のみ指定可能です。'})
	imagetype = forms.ChoiceField(widget=forms.RadioSelect())

	# フィールドの日本語名辞書
	nameDic = {"image_name":u"OSイメージ名", "image_description":u"説明","bucket_name":u"バケット名","imagetype":u"イメージタイプ"}

	def is_valid(self):
		if not self.errors:
			return True

		#エラーメッセージのフィールド名を日本語に置換
		for name in self.errors.keys():
			msgs = self.errors.pop(name)
			displayName = self.nameDic[name]
			error_list = forms.util.ErrorList()
			for msg in msgs:
				error_list.append( u"%s： %s" % (displayName, msg) )
			self.errors[displayName] = error_list

		return False

class ImageCreateStep2Form(forms.Form):
	kernel = forms.ChoiceField(widget=forms.Select(),error_messages={'required': u'カーネルイメージIDを入力してください。'})
	ramdisk = forms.ChoiceField(widget=forms.Select(),error_messages={'required': u'ラムディスクイメージIDを入力してください。'})
	image_path = CustomFilePathField(path=euca_common.createImagePath(),error_messages={'required': u'イメージファイルを入力してください。'})

	# フィールドの日本語名辞書
	nameDic = {"kernel":u"カーネルイメージID", "ramdisk":u"ラムディスクイメージID","image_path":u"イメージファイル"}

	def is_valid(self):
		if not self.errors:
			return True

		#エラーメッセージのフィールド名を日本語に置換
		for name in self.errors.keys():
			msgs = self.errors.pop(name)
			displayName = self.nameDic[name]
			error_list = forms.util.ErrorList()
			for msg in msgs:
				error_list.append( u"%s： %s" % (displayName, msg) )
			self.errors[displayName] = error_list

		return False

class ImagePublicRangeForm(forms.Form):
	publicrange = forms.ChoiceField(widget=forms.RadioSelect(),error_messages={'required': u'公開範囲を入力してください。'})

	# フィールドの日本語名辞書
	nameDic = {"publicrange":u"公開範囲"}

	def is_valid(self):
		if not self.errors:
			return True

		#エラーメッセージのフィールド名を日本語に置換
		for name in self.errors.keys():
			msgs = self.errors.pop(name)
			displayName = self.nameDic[name]
			error_list = forms.util.ErrorList()
			for msg in msgs:
				error_list.append( u"%s： %s" % (displayName, msg) )
			self.errors[displayName] = error_list

		return False
