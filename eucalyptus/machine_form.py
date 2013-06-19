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
from models import MachineGroup, Machine
from django.forms.formsets import BaseFormSet


class GroupIdForm(forms.Form):
	group_id = forms.IntegerField(widget=forms.HiddenInput)


class MachineGroupForm(forms.ModelForm):
	"""仮想サーバグループのモデルフォーム"""
	class Meta:
		model = MachineGroup
		exclude = ('account_id', 'user_id')

	def __init__(self, *args, **kwargs):
		super(MachineGroupForm, self).__init__(*args, **kwargs) # Call to ModelForm constructor
		self.fields['name'].widget.attrs.update({'size':'60'})
		#self.fields['name'].error_messages={'required': u'仮想マシングループ名を入力してください。'}
		self.fields['description'].widget.attrs.update({'size':'60'})

	# フィールドの日本語名辞書
	nameDic = {"name":u"仮想サーバグループ名", "description":u"説明" }

	# エラーメッセージ変更. is_valid のオーバーライド以外で行えるなら差し替え
	def is_valid(self):
		if not self.errors:
			return True

		#エラーメッセージ本体に日本語フィールド名を埋め込み
		for name in self.errors.keys():
			msgs = self.errors.pop(name)
			displayName = self.nameDic[name]
			error_list = forms.util.ErrorList()
			for msg in msgs:
				error_list.append( u"%s： %s" % (displayName, msg) )
			self.errors[displayName] = error_list

		return False


class MachineForm(forms.ModelForm):
	"""仮想サーバのモデルフォーム"""
	class Meta:
		model = Machine


class BaseMachineFormSet1(BaseFormSet):
	"""step1.テンプレート選択の可変長フォーム"""
	def add_fields(self, form, index):
		super(BaseMachineFormSet1, self).add_fields(form, index)
		#削除
		form.fields.pop("group")
		form.fields.pop("instance_id")
		form.fields.pop("ip")
		form.fields.pop("keypair")
		form.fields.pop("security_group")
		form.fields.pop("avaulability_zone")
		form.fields.pop("user_data")
		#追加
		form.fields["template_name"] = forms.CharField(widget=forms.HiddenInput, label=None)
		#属性変更
		form.fields['name'].widget.attrs.update({"size":"60"})
		#フィールド変更
		form.fields['image_id'] = forms.CharField(widget=forms.HiddenInput)
		form.fields['vmtype'] = forms.CharField(widget=forms.HiddenInput)
		form.fields['template_id'] = forms.IntegerField(widget=forms.HiddenInput)
		form.fields['order'] = forms.IntegerField(widget=forms.HiddenInput)

	# フィールドの日本語名辞書
	nameDic = {"name":u"仮想サーバ名", "image_id":u"イメージID", "vmtype":u"起動タイプ",
				"template_id":u"テンプレートID", "order":u"表示順", "template_name":u"テンプレート名" }

	# エラーメッセージ変更. is_valid のオーバーライド以外で行えるなら差し替え
	def is_valid(self):
		if super(BaseMachineFormSet1, self).is_valid():
			return True

		#エラーメッセージ本体に日本語フィールド名を埋め込み
		for i in range(0, self.total_form_count()):
			form = self.forms[i]
			for name in form.errors.keys():
				msgs = form.errors.pop(name)
				displayName = self.nameDic[name]
				error_list = forms.util.ErrorList()
				for msg in msgs:
					error_list.append( u"%s： %s" % (displayName, msg) )
				form.errors[displayName] = error_list

		return False

class MachineEditForm(forms.Form):
	"""step2.仮想マシン設定のフォーム"""
	name = forms.CharField(widget=forms.HiddenInput,required=False)
	order = forms.IntegerField(widget=forms.HiddenInput)
	ip = forms.ChoiceField(required=False)
	vmtype = forms.ChoiceField()
	#volume = forms.ChoiceField(required=False)
	volume = forms.ChoiceField(required=False, widget=forms.Select(attrs={'onchange':'enableCreateVolume(form);'}))

	volume_size = forms.IntegerField(required=False,error_messages={'invalid': u'ボリューム作成サイズに整数を入力してください。'})
	volume_size.widget.attrs['class'] = 'volume_size'
	volume_zone = forms.ChoiceField(required=False)

	#vol = forms.ChoiceField(widget=forms.RadioSelect(),required=False)
	#vol_name = forms.CharField(max_length=256,widget=forms.TextInput(attrs={'size':'60'}),required=False)
	#vol_size = forms.DecimalField(max_value=10,required=False)
	#vol_select = forms.ChoiceField(required=False)
	keypair = forms.ChoiceField(required=False,initial='yourkey')
	security_group = forms.ChoiceField(required=False,initial='defalut')
	avaulability_zone = forms.ChoiceField(required=False)
	user_data = forms.CharField(max_length=1024,widget=forms.Textarea(attrs={'cols':'60', 'rows':'4'}),required=False)

	# フィールドの日本語名辞書
	nameDic = {"name":u"仮想サーバ名", "order":u"表示順", "ip":u"IPアドレス", "vmtype":u"起動タイプ",
				"volume":u"データボリューム", "volume_size":u"データボリューム", "keypair":u"仮想マシン接続鍵", "security_group":u"ファイアウォール",
				"avaulability_zone":u"Avaulability Zone", "user_data":u"ユーザーデータ" }

	# エラーメッセージ変更. is_valid のオーバーライド以外で行えるなら差し替え
	def is_valid(self):
		if not self.errors:
			return True

		#エラーメッセージ本体に日本語フィールド名を埋め込み
		for name in self.errors.keys():
			msgs = self.errors.pop(name)
			displayName = self.nameDic[name]
			error_list = forms.util.ErrorList()
			for msg in msgs:
				error_list.append( u"%s： %s" % (displayName, msg) )
			self.errors[displayName] = error_list

		return False
	
	def set_keypair(self, keypair):
		self.keypair = forms.ChoiceField(required=False,initial=keypair)

class MachineDetailForm(forms.Form):
	"""step2.詳細設定"""
	detail = forms.BooleanField(widget=forms.HiddenInput)
