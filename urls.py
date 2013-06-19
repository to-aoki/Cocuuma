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
#

from django.conf.urls.defaults import patterns, include, url

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    # Examples:
    # url(r'^$', 'koala.views.home', name='home'),
    # url(r'^koala/', include('koala.foo.urls')),

    # Uncomment the admin/doc line below to enable admin documentation:
    # url(r'^admin/doc/', include('django.contrib.admindocs.urls')),
    # Uncomment the next line to enable the admin:
	url(r'^login/dologin/','koala.eucalyptus.login_views.dologin'),
    url(r'^logout/','koala.eucalyptus.login_views.logout'),
    url(r'^login/','koala.eucalyptus.login_views.login'),
    url(r'^template/modtemplate/','koala.eucalyptus.template_views.mod'),
    url(r'^template/domodtemplate/','koala.eucalyptus.template_views.domod'),
    url(r'^template/createtemplate/','koala.eucalyptus.template_views.create'),
    url(r'^template/docreatetemplate/','koala.eucalyptus.template_views.docreate'),
    url(r'^template/deltemplate/','koala.eucalyptus.template_views.delete'),
	url(r'^template/(?P<template_id>\S+)/$','koala.eucalyptus.template_views.top'),
	url(r'^machine/choice/(?P<group_id>\d+)/$','koala.eucalyptus.machine_views.choice'),
	url(r'^machine/grouprun/$','koala.eucalyptus.machine_views.grouprun'),
	url(r'^machine/groupterminate/$','koala.eucalyptus.machine_views.groupterminate'),
	url(r'^machine/groupdelete/$','koala.eucalyptus.machine_views.groupdelete'),
	url(r'^machine/autorefresh/$','koala.eucalyptus.machine_views.autorefresh'),
	url(r'^machine/refresh/$','koala.eucalyptus.machine_views.refresh'),
	url(r'^machine/groupcreate/$','koala.eucalyptus.machine_views.groupcreate'),
	url(r'^machine/groupupdate/$','koala.eucalyptus.machine_views.groupupdate'),
	url(r'^machine/addtemplate/$','koala.eucalyptus.machine_views.addTemplate'),
	url(r'^machine/step1end/$','koala.eucalyptus.machine_views.step1end'),
	url(r'^machine/step2select/(?P<order>\d+)/$','koala.eucalyptus.machine_views.step2select'),
	url(r'^machine/step1back/$','koala.eucalyptus.machine_views.step1back'),
	url(r'^machine/getip/$','koala.eucalyptus.machine_views.getip'),
	url(r'^machine/step2detail/$','koala.eucalyptus.machine_views.step2detail'),
	url(r'^machine/step2end/$','koala.eucalyptus.machine_views.step2end'),
	url(r'^machine/step2back/$','koala.eucalyptus.machine_views.step2back'),
	url(r'^machine/step3run/$','koala.eucalyptus.machine_views.step3run'),
	url(r'^machine/step3save/$','koala.eucalyptus.machine_views.step3save'),
	url(r'^machine/cancel/$','koala.eucalyptus.machine_views.cancel'),
	url(r'^machine/machinerun/(?P<machine_id>\d+)/$','koala.eucalyptus.machine_views.machinerun'),
	url(r'^machine/machineterminate/(?P<machine_id>\d+)/$','koala.eucalyptus.machine_views.machineterminate'),
	url(r'^machine/machinestop/(?P<machine_id>\d+)/$','koala.eucalyptus.machine_views.machinestop'),
	url(r'^machine/machinestart/(?P<machine_id>\d+)/$','koala.eucalyptus.machine_views.machinestart'),
	url(r'^machine/getconsole/(?P<instance_id>\S+)/$','koala.eucalyptus.machine_views.get_console'),
	url(r'^machine/','koala.eucalyptus.machine_views.top'),
	url(r'^dashboard/credentials/$','koala.eucalyptus.dashboard_views.credentials'),
    url(r'^dashboard/keypair/$','koala.eucalyptus.dashboard_views.keypair'),
	url(r'^dashboard/','koala.eucalyptus.dashboard_views.top'),
	url(r'^address/allocate/$','koala.eucalyptus.address_views.allocate'),
	url(r'^address/disassociate/(?P<ip>\d+\.\d+\.\d+\.\d+)/$','koala.eucalyptus.address_views.disassociate'),
	url(r'^address/release/(?P<ip>\d+\.\d+\.\d+\.\d+)/$','koala.eucalyptus.address_views.release'),
	url(r'^address/','koala.eucalyptus.address_views.top'),
	url(r'^volume/choice/(?P<index>\d+)/$','koala.eucalyptus.volume_views.choice'),
    url(r'^volume/choiceroot/(?P<index>\d+)/$','koala.eucalyptus.volume_views.choice_root'),
	url(r'^volume/refresh/$','koala.eucalyptus.volume_views.refresh'),
	url(r'^volume/update/$','koala.eucalyptus.volume_views.update'),
	url(r'^volume/delete/$','koala.eucalyptus.volume_views.delete'),
	url(r'^volume/createform/$','koala.eucalyptus.volume_views.createform'),
    url(r'^volume/createformfromsnapshot/$','koala.eucalyptus.volume_views.createform_from_snapshot'),
	url(r'^volume/create/$','koala.eucalyptus.volume_views.create'),
	url(r'^volume/attachselect/$','koala.eucalyptus.volume_views.attachselect'),
	url(r'^volume/attach/$','koala.eucalyptus.volume_views.attach'),
	url(r'^volume/detach/$','koala.eucalyptus.volume_views.detach'),
	url(r'^volume/createsnapshot/$','koala.eucalyptus.volume_views.createsnapshot'),
	url(r'^volume/snapshot/refresh/$','koala.eucalyptus.volume_views.snapshot_refresh'),
	url(r'^volume/snapshot/delete/$','koala.eucalyptus.volume_views.snapshot_delete'),
	url(r'^volume/snapshot/(?P<index>\d+)/$','koala.eucalyptus.volume_views.snapshot'),
	url(r'^volume/cancel/$','koala.eucalyptus.volume_views.cancel'),
	url(r'^volume/','koala.eucalyptus.volume_views.top'),
	url(r'^keypair/create/$','koala.eucalyptus.keypair_views.create'),
	url(r'^keypair/delete/(?P<keyname>\S+)/$','koala.eucalyptus.keypair_views.delete'),
	url(r'^keypair/download/(?P<keyname>\S+)/$','koala.eucalyptus.keypair_views.download'),
	url(r'^keypair/','koala.eucalyptus.keypair_views.top'),
	url(r'^securitygroup/createform/$','koala.eucalyptus.securitygroup_views.createform'),
	url(r'^securitygroup/create/$','koala.eucalyptus.securitygroup_views.create'),
	url(r'^securitygroup/delete/(?P<groupname>\S+)/$','koala.eucalyptus.securitygroup_views.delete'),
	url(r'^securitygroup/modify/(?P<groupname>\S+)/$','koala.eucalyptus.securitygroup_views.modify'),
	url(r'^securitygroup/ruledel/(?P<rule_num>\d+)/$','koala.eucalyptus.securitygroup_views.ruledel'),
	url(r'^securitygroup/ruleadd/$','koala.eucalyptus.securitygroup_views.ruleadd'),
	url(r'^securitygroup/','koala.eucalyptus.securitygroup_views.top'),
	url(r'^image/modpublicrange/$','koala.eucalyptus.image_views.modpublicrange'),
	url(r'^image/domodpublicrange/$','koala.eucalyptus.image_views.domodpublicrange'),
	url(r'^image/createstep1/$','koala.eucalyptus.image_views.createstep1'),
	url(r'^image/createstep2/$','koala.eucalyptus.image_views.createstep2'),
	url(r'^image/createstep1end/$','koala.eucalyptus.image_views.createstep1end'),
	url(r'^image/createstep1back/$','koala.eucalyptus.image_views.createstep1back'),
	url(r'^image/createstep2back/$','koala.eucalyptus.image_views.createstep2back'),
	url(r'^image/createstep3/$','koala.eucalyptus.image_views.createstep3'),
	url(r'^image/delete/$','koala.eucalyptus.image_views.delete'),
	url(r'^image/(?P<image_id>\S+)/$','koala.eucalyptus.image_views.top'),
    url(r'^report/','koala.eucalyptus.report_views.top'),
	url(r'^admin/', include(admin.site.urls)),
	url(r'^$','koala.eucalyptus.login_views.login'),

    # 管理メニュー
    url(r'^resource/instancelist/$','koala.eucalyptus.resource_views.instance_view'),
    url(r'^resource/accountlist/$','koala.eucalyptus.resource_views.account_list'),
    url(r'^resource/accountinfo/$','koala.eucalyptus.resource_views.account_info'),
    url(r'^resource/hostlist/$','koala.eucalyptus.resource_views.host_view'),
    url(r'^resource/nodeinfo/$','koala.eucalyptus.resource_views.node_info'),
    url(r'^resource/volumelist/$','koala.eucalyptus.resource_views.volume_view'),
    url(r'^resource/volumedelete/(?P<vol_id>\S+)/$','koala.eucalyptus.resource_views.volume_delete'),
    url(r'^resource/volumedeletefile/(?P<vol_id>\S+)/$','koala.eucalyptus.resource_views.volume_delete_file'),
    url(r'^resource/volumedeletedb/(?P<vol_id>\S+)/$','koala.eucalyptus.resource_views.volume_delete_db'),
    url(r'^resource/snapshotlist/$','koala.eucalyptus.resource_views.snapshot_view'),
    url(r'^resource/propertylist/$','koala.eucalyptus.resource_views.properties_view'),
    # 拡張機能
    url(r'^vmmonitoron/(?P<machine_id>\d+)/$','koala.eucalyptus.machine_views.vmmonitoron'),
    url(r'^vmmonitoroff/(?P<machine_id>\d+)/$','koala.eucalyptus.machine_views.vmmonitoroff'),

    #アクセス管理メニュー
    url(r'^user_manage/$','koala.eucalyptus.user_manage_views.user_manage_view'),
    url(r'^user_manage/group/$','koala.eucalyptus.user_manage_views.group_manage_view'),
    url(r'^user_manage/group/createform/$','koala.eucalyptus.user_manage_views.creategroupform'),
    url(r'^user_manage/group/create/$','koala.eucalyptus.user_manage_views.groupcreate'),
    url(r'^user_manage/policy_set/$','koala.eucalyptus.user_manage_views.policy_set_view'),
    url(r'^user_manage/group/groupinfo/$','koala.eucalyptus.user_manage_views.group_info'),
)
