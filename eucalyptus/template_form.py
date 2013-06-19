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

class TemplateModForm(forms.Form):
    name = forms.CharField(max_length=256,widget=forms.TextInput(attrs={'class':'text'}),error_messages={'required': u'テンプレート名を入力してください。','max_length': u'256文字以下で入力してください。'})
    description = forms.CharField(required=False,max_length=256,widget=forms.TextInput(attrs={'class':'text'}),error_messages={'max_length': u'256文字以下で入力してください。'})
    image = forms.ChoiceField(widget=forms.Select())
    vmtype = forms.ChoiceField(widget=forms.Select())
    count = forms.IntegerField(min_value = 1,max_value = 10,widget=forms.TextInput(attrs={'class':'text'}),
                               error_messages={'required': u'起動台数を入力してください。','invalid': u'1以上10以下の整数を入力してください。','min_value': u'1以上10以下の整数を入力してください。','max_value': u'1以上10以下の整数を入力してください。'})

    # フィールドの日本語名辞書
    nameDic = {"name":u"テンプレート名", "description":u"説明", "image":u"イメージ名", "vmtype" :u"起動タイプ", "count":u"起動台数" }

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
