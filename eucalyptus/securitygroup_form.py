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
import re


# 半角英数(ASCII)チェック
regexp = re.compile(r'^[\x20-\x7E]+$')

class CreateForm(forms.Form):
	name = forms.CharField(label=u"名前",max_length=30,widget=forms.TextInput(attrs={'size':'30'}),error_messages={'required': u'名前を入力してください。'})
	description = forms.CharField(max_length=256,widget=forms.TextInput(attrs={'size':'80'}),error_messages={'required': u'説明を入力してください。'})
	defaultrule = forms.BooleanField(required=False,label=u"以下のルールを設定する")

	def clean_name(self):
		_name = self.cleaned_data['name']
		if regexp.match(_name) == None:
			raise forms.ValidationError(u"名前は半角英数字で入力して下さい。")
		else:
			return _name

	def clean_description(self):
		_description = self.cleaned_data['description']
		if regexp.match(_description) == None:
			raise forms.ValidationError(u"説明は半角英数字で入力して下さい。")
		else:
			return _description


class ModifyForm(forms.Form):
	addType = forms.ChoiceField(choices=[('address',u'外部接続'),('group',u'ファイアウォール間接続')],widget=forms.RadioSelect())
	protocol = forms.ChoiceField(required=False,choices=[('tcp','TCP/IP'),('udp','UDP/IP'),('icmp','ICMP')],widget=forms.Select(attrs={'class':'outer outer_connect'}))
	portMin = forms.IntegerField(required=False,widget=forms.TextInput(attrs={'size':'5', 'class':'outer outer_connect'}))
	portMax = forms.IntegerField(required=False,widget=forms.TextInput(attrs={'size':'5', 'class':'outer outer_connect'}))
	cidr = forms.CharField(required=False,widget=forms.TextInput(attrs={'class':'outer outer_connect'}))
	fromUser = forms.CharField(required=False,widget=forms.TextInput(attrs={'class':'inner inner_connect'}))
	fromGroup = forms.CharField(required=False,widget=forms.TextInput(attrs={'class':'inner inner_connect'}))
