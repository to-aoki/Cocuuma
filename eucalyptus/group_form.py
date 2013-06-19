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


class GroupForm(forms.Form):
	group_id = forms.CharField(widget=forms.HiddenInput)
	group_name = forms.CharField(max_length=256,widget=forms.TextInput(attrs={'size':'80'}),error_messages={'required': u'グループ名を入力してください。'})
	group_desc = forms.CharField(required=False,max_length=256,widget=forms.TextInput(attrs={'size':'80'}))
	group_path = forms.CharField(required=False,max_length=256,widget=forms.TextInput(attrs={'size':'80'}))
	group_polset = forms.ChoiceField()

	# フィールドの日本語名辞書
	nameDic = {"group_id":u"グループID", "group_name":u"グループ名", "group_desc":u"説明", group_polset:u"権限セット"}

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

#class VolumeAttachForm(forms.Form):
#	machine = forms.IntegerField(widget=forms.Select())
#	device = forms.CharField(initial='/dev/vdb',max_length=256,widget=forms.TextInput(attrs={'size':'15'}),error_messages={'required': u'デバイス名を入力してください。'})

class GroupCreateForm(forms.Form):
	group_name = forms.CharField(max_length=256,widget=forms.TextInput(attrs={'size':'80'}),error_messages={'required': u'グループ名を入力してください。'})
	group_desc = forms.CharField(required=False,max_length=256,widget=forms.TextInput(attrs={'size':'80'}))
	group_path = forms.CharField(required=False,max_length=256,widget=forms.TextInput(attrs={'size':'80'}))
	account_name = forms.CharField(required=False,max_length=256,widget=forms.TextInput(attrs={'size':'80'}))
	#account_name = forms.CharField(required=False,max_length=256,widget=forms.HiddenInput)
	group_polset = forms.ChoiceField()
	
	
class GroupDeleteForm(forms.Form):
	del_check = forms.BooleanField(required=False)
	group_name = forms.CharField(max_length=256,widget=forms.TextInput(attrs={'size':'80'}),error_messages={'required': u'グループ名を入力してください。'})
	group_desc = forms.CharField(required=False,max_length=256,widget=forms.TextInput(attrs={'size':'80'}))
	group_path = forms.CharField(required=False,max_length=256,widget=forms.TextInput(attrs={'size':'80'}))
	account_name = forms.CharField(required=False,max_length=256,widget=forms.TextInput(attrs={'size':'80'}))
	#account_name = forms.CharField(required=False,max_length=256,widget=forms.HiddenInput)
	group_polset = forms.ChoiceField()

