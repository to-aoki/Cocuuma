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


# Create your views here.
#from django.utils.dateparse import parse_datetime
from django.template import RequestContext
#from django.template import Context, loader
from django.shortcuts import render_to_response
from django.http import HttpResponse, HttpResponseRedirect
#from resource_models import Instance_information
from euca_access import GetEucalyptusInfo, GetEucalyptusInfoBy2ool
from db_access import EucalyptusDB
from db_access_metadata import EucalyptusMetadataDB
from resource_models import *
from monitor_models import Monitorings
from zab_monitor_access import ZabbixAccess
import re
import euca_common
from server_access import ServerAccess
from datetime import datetime
import time

import logging
#カスタムログ
logger = logging.getLogger('koalalog')

def filter_ins(raw_list,status,account,node):
	if status != "all":
		filtered_list = []
		for ins in raw_list:
			if ins.status == status:
				filtered_list.append(ins)
		raw_list = filtered_list
	if account != "all":
		filtered_list = []
		for ins in raw_list:
			if ins.account == account:
				filtered_list.append(ins)
		raw_list = filtered_list
	if node != "all":
		filtered_list = []
		for ins in raw_list:
			if ins.node == node and ins.using_resources():
				filtered_list.append(ins)
		raw_list = filtered_list
	return raw_list

def filter_vol(raw_list,account):
	if account != "all":
		filtered_list = []
		for vol in raw_list:
			if vol.accountid == account:
				filtered_list.append(vol)
		raw_list = filtered_list
	return raw_list

def filter_snap(raw_list,account):
	if account != "all":
		filtered_list = []
		for snap in raw_list:
			if snap.accountname == account:
				filtered_list.append(snap)
		raw_list = filtered_list
	return raw_list

def sort_res_list(raw_list,sort_dir,key):
	if sort_dir == '1':
		return sorted(raw_list,key=lambda x:x[key])
	else:
		return sorted(raw_list,key=lambda x:x[key],reverse=True)

# ソート語句
def sort_ins(raw_list, request):
	if request.session['sortins'] != '0':
		return sort_res_list(raw_list,request.session['sortins'],'instanceid')
	if request.session['sortacc'] != '0':
		return sort_res_list(raw_list,request.session['sortacc'],'account')
	if request.session['sortnod'] != '0':
		return sort_res_list(raw_list,request.session['sortnod'],'node')
	if request.session['sortroo'] != '0':
		return sort_res_list(raw_list,request.session['sortroo'],'rootdevicetype')
	return raw_list

def sort_vol(raw_list,request):
	if request.session['sortins'] != '0':
		return sort_res_list(raw_list,request.session['sortins'],'instanceid')
	if request.session['sortacc'] != '0':
		return sort_res_list(raw_list,request.session['sortacc'],'accountid')
	if request.session['sortvol'] != '0':
		return sort_res_list(raw_list,request.session['sortvol'],'volumeid')
	if request.session['sortsnap'] != '0':
		return sort_res_list(raw_list,request.session['sortsnap'],'snapshotid')
	return raw_list

def sort_snap(raw_list,request):
	if request.session['sortsnap'] != '0':
		return sort_res_list(raw_list,request.session['sortsnap'],'snapshotid')
	if request.session['sortacc'] != '0':
		return sort_res_list(raw_list,request.session['sortacc'],'accountname')
	if request.session['sortvol'] != '0':
		return sort_res_list(raw_list,request.session['sortvol'],'volumeid')
	if request.session['sortstat'] != '0':
		return sort_res_list(raw_list,request.session['sortstat'],'status')
	if request.session['sorttime'] != '0':
		return sort_res_list(raw_list,request.session['sorttime'],'starttime')
	return raw_list

def sort_acc(raw_list,request):
	if request.session['sortname'] != '0':
		return sort_res_list(raw_list,request.session['sortname'],'accountname')
	if request.session['sortcpu'] != '0':
		return sort_res_list(raw_list,request.session['sortcpu'],'cpu')
	if request.session['sortmem'] != '0':
		return sort_res_list(raw_list,request.session['sortmem'],'mem')
	if request.session['sortvol'] != '0':
		return sort_res_list(raw_list,request.session['sortvol'],'total_volume_size')
	return raw_list

def sort_node(raw_list,request):
	if request.session['sortip'] != '0':
		return sort_res_list(raw_list,request.session['sortip'],'node_ip')
	if request.session['sortinsnum'] != '0':
		return sort_res_list(raw_list,request.session['sortinsnum'],'num_ins')
	if request.session['sortcpu'] != '0':
		return sort_res_list(raw_list,request.session['sortcpu'],'cpu')
	if request.session['sortmem'] != '0':
		return sort_res_list(raw_list,request.session['sortmem'],'mem')
	return raw_list

def relate_volume(request, volumeOwner):

	for vol in request.session['res_volumes']:
		vol.accountnumber = None
		for own in volumeOwner:
			if own.volumeid == vol.volumeid:
				vol.accountnumber = own.account_number
				break
		acc_name = None
		if vol.accountnumber:
			for acc in request.session['res_accounts']:
				if acc.accountid == vol.accountnumber:
					acc_name = acc.accountname
					break
		vol.accountid = acc_name
		#logger.debug("volume %s owner %s" % (vol.volumeid, vol.accountid))

	vol_file_data_list = []
	for host in request.session['res_frontends']:
		if host.has_sc():
			sa = ServerAccess(host.server_ip)
			if sa.hostname():
				vol_file_data = {}
				vol_file_data['filelist'] = sa.getFileList(host.volume_path, "vol-")
				vol_file_data['partition'] = host.getScPartition()
				vol_file_data_list.append(vol_file_data)
				logger.debug("volume file list (%s):%d" % (vol_file_data['partition'], len(vol_file_data['filelist'])))

	if vol_file_data_list:
		for vol in request.session['res_volumes']:
			vol.filefound = False
			for data in vol_file_data_list:
				for vol_file in data['filelist']:
					if vol_file.filename == vol.volumeid:
						vol.filefound = True
						vol_file.valid = True
						break
				if not vol.filefound and not vol.deletingOrDeleted():
					vol.status = "file not found"

		for data in vol_file_data_list:
			for vol_file in data['filelist']:
				if not vol_file.valid:
					vol = Volume_information()
					vol.volumeid = vol_file.filename
					vol.filefound = False
					vol.status = "invalid file"
					vol.size = int(vol_file.size)/1024/1024/1024
					vol.partition = data['partition']
					vol.accountid = None
					vol.accountnumber = None
					vol.snapshotid = None
					vol.instanceid = None
					request.session['res_volumes'].append(vol)

	return request.session['res_volumes']

def relate_snapshot(request):
	for snap in request.session['res_snapshots']:
		for acc in request.session['res_accounts']:
			if acc.accountid == snap.accountid:
				snap.accountname = acc.accountname
				break

	return request.session['res_snapshots']

def relate_instance(request):

	for ins in request.session['res_instances']:
		ins.attachedvolumes = []
		for vol in request.session['res_volumes']:
			if vol.instanceid == ins.instanceid:
				ins.attachedvolumes.append(vol.volumeid)
		for n in request.session['res_nodes']:
			for i in n.instanceids:
				if i == ins.instanceid:
					ins.node = n.node_ip
		for acc in request.session['res_accounts']:
			if ins.accountid == acc.accountid:
				ins.account = acc.accountname
		for v in request.session['res_vmtypes']:
			if ins.vmtype == v.vmtype:
				ins.cpu = v.cpu
				ins.mem = v.mem
				ins.disk = v.disk

	return request.session['res_instances']

def relate_account(request):

	for acc in request.session['res_accounts']:
		acc.total_volume_size = 0
		for vol in request.session['res_volumes']:
			if vol.accountid == acc.accountname:
				acc.total_volume_size += int(vol.size)
		acc.num_instances = 0
		acc.num_all_instances = 0
		acc.cpu = 0
		acc.mem = 0
		for ins in request.session['res_instances']:
			if ins.accountid == acc.accountid:
				acc.num_all_instances += 1
				if ins.using_resources():
					acc.num_instances += 1
					acc.cpu += int(ins.cpu)
					acc.mem += int(ins.mem)

	return request.session['res_accounts']

def relate_node(request):

	# 暫定的にvmtypeから逆算
	all_cpus = all_mems = node_max_cpu = node_max_mem = 0
	for vt in request.session['res_vmtypes']:
		vt_all_cpus = int(vt.max)*int(vt.cpu)
		if vt_all_cpus > all_cpus:
			all_cpus = vt_all_cpus
		vt_all_mems = int(vt.max)*int(vt.mem)
		if vt_all_mems > all_mems:
			all_mems = vt_all_mems
	if len(request.session['res_nodes']) > 0:
		node_max_cpu = all_cpus/len(request.session['res_nodes'])
		node_max_mem = all_mems/len(request.session['res_nodes'])
		#logger.debug("max cpu/mem : all %s/%s : node %s/%s" % (all_cpus, all_mems, node_max_cpu, node_max_mem))

	for node in request.session['res_nodes']:
		node.cpu = 0
		node.mem = 0
		node.max_cpu = node_max_cpu
		node.max_mem = node_max_mem
		node.instanceids = []
		for ins in request.session['res_instances']:
			if ins.node == node.node_ip and ins.using_resources():
				node.cpu += int(ins.cpu)
				node.mem += int(ins.mem)
				node.instanceids.append(ins.instanceid)

	return request.session['res_nodes']

def relate_frontends(request):
	for host in request.session['res_frontends']:
		if host.has_sc():
			host.volume_path = re.sub('//','/', getPropertyValue(request, host.getScPartition() + '.storage.volumesdir'))
		if host.has_walrus():
			host.walrus_path = re.sub('//','/', getPropertyValue(request, 'walrus.storagedir'))

def getData(request, login_user):

	logger.debug("getData begin")
	tool = GetEucalyptusInfoBy2ool()
	request.session['res_instances'] = tool.getInstanceListVerbose(login_user)
	request.session['res_volumes'] = tool.getVolumeListVerbose(login_user)
	request.session['res_snapshots'] = tool.getSnapshotListVerbose(login_user)
	request.session['res_nodes'] = tool.getNodeList(login_user)
	request.session['res_frontends'] = tool.getServices(login_user)
	request.session['cloud_properties'] = tool.getCloudProperties(login_user)

	eucadb = EucalyptusDB()
	acc_list = eucadb.getAccountList()
	acc_info_list = []
	for acc in acc_list:
		acc_info = Account_information()
		acc_info.accountname = acc.name
		acc_info.accountid = acc.id_number
		acc_info_list.append(acc_info)
	request.session['res_accounts'] = acc_info_list

	boto = GetEucalyptusInfo()
	request.session['res_vmtypes'] = boto.get_vmtypes(login_user.db_user)

	eucaMetaDB = EucalyptusMetadataDB()
	volumeOwner = eucaMetaDB.getVolumeOwnerList()

	relate_frontends(request)
	relate_volume(request, volumeOwner)
	relate_snapshot(request)
	relate_instance(request)
	relate_account(request)
	relate_node(request)
	request.session.modified = True
	request.session['res_last_update'] = datetime.now()
	logger.debug("getData end")

def init_params(request):
	if not 'sortins' in request.session:
		request.session['sortins'] = '0'
	if not 'sortacc' in request.session:
 		request.session['sortacc'] = '0'
	if not 'sortnod' in request.session:
		request.session['sortnod'] = '0'
	if not 'sortroo' in request.session:
		request.session['sortroo'] = '0'
	if not 'data_extract' in request.session:
		request.session['data_extract'] = 'none'
	if not 'filer_status' in request.session:
		request.session['filter_status'] = 'all'
	if not 'sortname' in request.session:
		request.session['sortname'] = '0'
	if not 'sortcpu' in request.session:
		request.session['sortcpu'] = '0'
	if not 'sortmem' in request.session:
		request.session['sortmem'] = '0'
	if not 'sortvol' in request.session:
		request.session['sortvol'] = '0'
	if not 'sortiphide' in request.session:
		request.session['sortip'] = '0'
	if not 'sortinsnumhide' in request.session:
		request.session['sortinsnum'] = '0'
	if not 'sortsnaphide' in request.session:
		request.session['sortsnap'] = '0'
	if not 'sorttimehide' in request.session:
		request.session['sorttime'] = '0'
	if not 'sortstathide' in request.session:
		request.session['sortstat'] = '0'

def set_params(request):
	if 'sortinshide' in request.POST:
		request.session['sortins']=request.POST['sortinshide']
	if 'sortacchide' in request.POST:
		request.session['sortacc']=request.POST['sortacchide']
	if 'sortnodhide' in request.POST:
		request.session['sortnod']=request.POST['sortnodhide']
	if 'sortroohide' in request.POST:
		request.session['sortroo']=request.POST['sortroohide']
	if 'extract' in request.POST:
		request.session['data_extract']=request.POST['extract']
	if 'status' in request.POST:
		request.session['filter_status']=request.POST['status']
	if 'sortnamehide' in request.POST:
		request.session['sortname']=request.POST['sortnamehide']
	if 'sortcpuhide' in request.POST:
		request.session['sortcpu']=request.POST['sortcpuhide']
	if 'sortmemhide' in request.POST:
		request.session['sortmem']=request.POST['sortmemhide']
	if 'sortvolhide' in request.POST:
		request.session['sortvol']=request.POST['sortvolhide']
	if 'sortiphide' in request.POST:
		request.session['sortip']=request.POST['sortiphide']
	if 'sortinsnumhide' in request.POST:
		request.session['sortinsnum']=request.POST['sortinsnumhide']
	if 'sortsnaphide' in request.POST:
		request.session['sortsnap']=request.POST['sortsnaphide']
	if 'sorttimehide' in request.POST:
		request.session['sorttime']=request.POST['sorttimehide']
	if 'sortstathide' in request.POST:
		request.session['sortstat']=request.POST['sortstathide']


def isRefresh(request):
	if 'resource_refresh' in request.POST and request.POST['resource_refresh'] == 'yes':
		return True
	if 'res_last_update' not in request.session:
		return True
	return False

# インスタンス画面抽出項目ソートのパラメーターの判断
def instance_view(request):

	#メニューを「テンプレート」に設定
	request.session['ss_sys_menu'] = "resource"
	request.session['ss_sys_resource_menu'] = "instance_list"
	#セッションからログインユーザ情報を取得する
	login_user = request.session['ss_usr_user']

	init_params(request)
	set_params(request)

	# get data
	if isRefresh(request):
		getData(request, login_user)

	#zabb = ZabbixAccess()

	account = "all"
	node = "all"
	filtered = filter_ins(request.session['res_instances'],request.session['filter_status'],account,node)
	instance_list = sort_ins(filtered,request)

	selected_instance = None
	if request.session['data_extract'] != "none":
		selected_instance = instance_list[int(request.session['data_extract'])].instanceid

	return render_to_response('resource_instance_view.html',
		{'instance_list': instance_list,
		'selected_instance':selected_instance},
		context_instance=RequestContext(request))

# インスタンス画面抽出項目ソートのパラメーターの判断
def account_list(request):

	#メニューを「テンプレート」に設定
	request.session['ss_sys_menu'] = "resource"
	request.session['ss_sys_resource_menu'] = "account_views"
	#セッションからログインユーザ情報を取得する
	login_user = request.session['ss_usr_user']

	init_params(request)
	set_params(request)

	# get data
	if isRefresh(request):
		getData(request, login_user)

	account_list = sort_acc(request.session['res_accounts'],request)

	return render_to_response('account_list.html',
		{'account_list': account_list},
		context_instance=RequestContext(request))

def account_info(request):

	#メニューを「テンプレート」に設定
	request.session['ss_sys_menu'] = "resource"
	request.session['ss_sys_resource_menu'] = "account_views"
	#セッションからログインユーザ情報を取得する
	login_user = request.session['ss_usr_user']

	init_params(request)
	set_params(request)
	
	if 'selected_account' in request.POST:
		selected_account = request.POST['selected_account']
	else:
		selected_account = "all"

	# get data
	if isRefresh(request):
		getData(request, login_user)

	node = "all"
	filtered = filter_ins(request.session['res_instances'],request.session['filter_status'],selected_account,node)
	instance_list = sort_ins(filtered,request)
	selected_instance = None
	if request.session['data_extract'] != "none":
		selected_instance = instance_list[int(request.session['data_extract'])].instanceid

	account_info = None
	for acc in request.session['res_accounts']:
		if acc.accountname == selected_account:
			account_info = acc
			break;

	return render_to_response('account_info.html',
		{'instance_list': instance_list,
		'account_info': account_info,
		'selected_account':selected_account,
		'selected_instance':selected_instance},
		context_instance=RequestContext(request))

def getPropertyValue(request,name):
	for p in request.session['cloud_properties']:
		if p.name == name:
			return p.value
	return None

def getMountPath(zabb, path, hostname):
	itemKey = 'vfs.fs.size[' + path + ',total]'
	if zabb.getItem(itemKey, hostname):
		return path
	(path,slash,rest) = path.rpartition('/')
	if not path:
		return "/"
	return getMountPath(zabb, path, hostname)

def getMonitoringsBySsh(request, frontend_list, node_list):

	for host in frontend_list:
		mon = Monitorings()
		sa = ServerAccess(host.server_ip)
		if sa.hostname():
			mon.isAvailable = True
			mon.cpu_used = round(100 - sa.getCpuPercent("idle"), 1)
			(total, free) = sa.getMemFree()
			mon.mem_total = round(float(total)/1024/1024/1024, 1)
			mon.mem_used = mon.mem_total - round(float(free)/1024/1024/1024, 1)
			(total, free, mount_path) = sa.getDiskFree("/var")
			mon.disk_var_total = round(float(total)/1024/1024/1024, 1)
			mon.disk_var_used = mon.disk_var_total - round(float(free)/1024/1024/1024, 1)
			if host.has_sc():
				(total, free, host.volume_mount_path) = sa.getDiskFree(host.volume_path)
				mon.disk_volume_total = round(float(total)/1024/1024/1024, 1)
				mon.disk_volume_used = mon.disk_volume_total - round(float(free)/1024/1024/1024, 1)
			if host.has_walrus():
				(total, free, host.walrus_mount_path) = sa.getDiskFree(host.walrus_path)
				mon.disk_walrus_total = round(float(total)/1024/1024/1024, 1)
				mon.disk_walrus_used = mon.disk_walrus_total - round(float(free)/1024/1024/1024, 1)
		host.monitoring = mon

	for host in node_list:
		mon = Monitorings()
		#	cooalaサーバから直接ノードに通信可能の場合は、以下のコメントを外してノードのssh監視を有効にしてください
		#	sa = ServerAccess(host.monitored_ip)
		#	if sa.hostname():
		#		mon.isAvailable = True
		#		mon.cpu_used = round(100 - sa.getCpuPercent("idle"), 1)
		#		(total, free) = sa.getMemFree()
		#		mon.mem_total = round(float(total)/1024/1024/1024, 1)
		#		mon.mem_used = mon.mem_total - round(float(free)/1024/1024/1024, 1)
		#		(total, free, mount_path) = sa.getDiskFree("/var")
		#		mon.disk_var_total = round(float(total)/1024/1024/1024, 1)
		#		mon.disk_var_used = mon.disk_var_total - round(float(free)/1024/1024/1024, 1)
		host.monitoring = mon

def getMonitorings(zabb, request, frontend_list, node_list):
	if zabb.isValid():
		cpus = zabb.getItem('system.cpu.util[,idle]')
		mems = zabb.getItem('vm.memory.size[available]')
		totalmems = zabb.getItem('vm.memory.size[total]')
		for host in frontend_list:
			mon = Monitorings()
			if zabb.hostname2id(host.monitored_hostname):
				mon.isAvailable = True
				mon.cpu_used = round(100 - float(zabb.itemByHostname(cpus, host.monitored_hostname)), 1)
				mon.mem_total = round(float(zabb.itemByHostname(totalmems, host.monitored_hostname))/1024/1024/1024, 1)
				mon.mem_used = mon.mem_total - round(float(zabb.itemByHostname(mems, host.monitored_hostname))/1024/1024/1024, 1)
				var_mount_path = getMountPath(zabb,"/var",host.monitored_hostname)
				itemKey = 'vfs.fs.size[' + var_mount_path + ',total]'
				total = zabb.getItem(itemKey, host.monitored_hostname)[0]['lastvalue']
				if total and total != "0":
					mon.disk_var_total = round(float(total)/1024/1024/1024, 1)
					itemKey = 'vfs.fs.size[' + var_mount_path + ',free]'
					mon.disk_var_used = mon.disk_var_total - round(float(zabb.getItem(itemKey, host.monitored_hostname)[0]['lastvalue'])/1024/1024/1024, 1)
				if host.has_sc():
					host.volume_mount_path = getMountPath(zabb,host.volume_path,host.monitored_hostname)
					itemKey = 'vfs.fs.size[' + host.volume_mount_path + ',total]'
					mon.disk_volume_total = round(float(zabb.getItem(itemKey, host.monitored_hostname)[0]['lastvalue'])/1024/1024/1024, 1)
					itemKey = 'vfs.fs.size[' + host.volume_mount_path + ',free]'
					mon.disk_volume_used = mon.disk_volume_total - round(float(zabb.getItem(itemKey, host.monitored_hostname)[0]['lastvalue'])/1024/1024/1024, 1)
				if host.has_walrus():
					host.walrus_mount_path = getMountPath(zabb,host.walrus_path,host.monitored_hostname)
					itemKey = 'vfs.fs.size[' + host.walrus_mount_path + ',total]'
					mon.disk_walrus_total = round(float(zabb.getItem(itemKey, host.monitored_hostname)[0]['lastvalue'])/1024/1024/1024, 1)
					itemKey = 'vfs.fs.size[' + host.walrus_mount_path + ',free]'
					mon.disk_walrus_used = mon.disk_walrus_total - round(float(zabb.getItem(itemKey, host.monitored_hostname)[0]['lastvalue'])/1024/1024/1024, 1)
			host.monitoring = mon

		for host in node_list:
			mon = Monitorings()
			if zabb.hostname2id(host.monitored_hostname):
				mon.isAvailable = True
				mon.cpu_used = round(100 - float(zabb.itemByHostname(cpus, host.monitored_hostname)), 1)
				mon.mem_total = round(float(zabb.itemByHostname(totalmems, host.monitored_hostname))/1024/1024/1024, 1)
				mon.mem_used = mon.mem_total - round(float(zabb.itemByHostname(mems, host.monitored_hostname))/1024/1024/1024, 1)
				var_mount_path = getMountPath(zabb,"/var",host.monitored_hostname)
				itemKey = 'vfs.fs.size[' + var_mount_path + ',total]'
				total = zabb.getItem(itemKey, host.monitored_hostname)[0]['lastvalue']
				if total and total != "0":
					mon.disk_var_total = round(float(total)/1024/1024/1024, 1)
					itemKey = 'vfs.fs.size[' + var_mount_path + ',free]'
					mon.disk_var_used = mon.disk_var_total - round(float(zabb.getItem(itemKey, host.monitored_hostname)[0]['lastvalue'])/1024/1024/1024, 1)
			host.monitoring = mon
	else:
		for host in frontend_list:
			mon = Monitorings()
			host.monitoring = mon
		for host in node_list:
			mon = Monitorings()
			host.monitoring = mon

def host_view(request):

	#メニューを「テンプレート」に設定
	request.session['ss_sys_menu'] = "resource"
	request.session['ss_sys_resource_menu'] = "node_views"
	#セッションからログインユーザ情報を取得する
	login_user = request.session['ss_usr_user']

	init_params(request)
	set_params(request)

	# get data
	if isRefresh(request):
		getData(request, login_user)
	if isRefresh(request) or not 'cloud_properties' in request.session:
		tool = GetEucalyptusInfoBy2ool()
		request.session['cloud_properties'] = tool.getCloudProperties(login_user)

	frontend_list = request.session['res_frontends']
	node_list = sort_node(request.session['res_nodes'],request)

	zabb = ZabbixAccess()
	if zabb.isValid():
		getMonitorings(zabb,request,frontend_list,node_list)
	else:
		getMonitoringsBySsh(request,frontend_list,node_list)
	isMonitored = True

	return render_to_response('host_list.html',
		{'node_list': node_list,
		'frontend_list': frontend_list,
		'isMonitored': isMonitored},
		context_instance=RequestContext(request))

def node_info(request):

	#メニューを「テンプレート」に設定
	request.session['ss_sys_menu'] = "resource"
	request.session['ss_sys_resource_menu'] = "node_views"
	#セッションからログインユーザ情報を取得する
	login_user = request.session['ss_usr_user']

	init_params(request)
	set_params(request)
	#(sortins, sortacc, sortnod, sortroo, extract, status) = ins_params(request)
	#logger.debug("extract:%s" % extract)
	if 'selected_node' in request.POST:
		selected_node = request.POST['selected_node']
	else:
		selected_node = "all"

	# get data
	if isRefresh(request):
		getData(request, login_user)

	account = "all"
	filtered = filter_ins(request.session['res_instances'],request.session['filter_status'],account,selected_node)
	instance_list = sort_ins(filtered,request)
	selected_instance = None
	if request.session['data_extract'] != "none":
		selected_instance = instance_list[int(request.session['data_extract'])].instanceid

	node_info = None
	for node in request.session['res_nodes']:
		if node.node_ip == selected_node:
			node_info = node
			logger.debug("instances on node:%s" % (node.num_instances()))
			break;

	return render_to_response('node_info.html',
		{'instance_list': instance_list,
		'node_info': node_info,
		'selected_node':selected_node,
		'selected_instance':selected_instance},
		context_instance=RequestContext(request))

def resource_admin_auth(request):
	login_user = request.session['ss_usr_user']
	if not login_user.resource_admin:
		return HttpResponseRedirect('/logout/')

def volume_delete(request, vol_id):
	resource_admin_auth(request)
	acc_num = None
	volume = None
	
	for vol in request.session['res_volumes']:
		if vol.volumeid == vol_id:
			acc_num = vol.accountnumber
			volume = vol
	if acc_num:
		euca_db = EucalyptusDB()
		usrList = euca_db.getEucalyptusUser()
		errors = []
		for usr in usrList:
			if usr.account_number == acc_num and usr.accesskey:
				try:
					get_euca_info=GetEucalyptusInfo(usr)
					get_euca_info.delete_volume(vol_id)
					volume.status = "deleting"
					request.session.modified = True
					
				except Exception, ex:
					# Eucalyptusエラー
					errors.append(euca_common.get_euca_error_msg('%s' % ex))
					logger.warn(errors)

	return volume_view(request)

def getSCHost(request,partition):
	for host in request.session['res_frontends']:
		if host.has_sc() and partition == host.getScPartition():
			return host
	return None

def getVolumeFromId(request,vol_id):
	for vol in request.session['res_volumes']:
		if vol.volumeid == vol_id:
			return vol
	return None

def volume_delete_file(request, vol_id):
	resource_admin_auth(request)
	vol = getVolumeFromId(request,vol_id)
	if vol and vol.status == "invalid file":
		sc_host = getSCHost(request,vol.partition)
		if sc_host:
			sa = ServerAccess(sc_host.server_ip, True)
			if sa.hostname():
				sa.deleteFile(sc_host.volume_path + "/" +vol_id)
				vol.status = "deleting"
				request.session.modified = True
				#request.POST['resource_refresh'] = 'yes'

	return volume_view(request)

def volume_delete_db(request, vol_id):
	resource_admin_auth(request)
	
	vol = getVolumeFromId(request,vol_id)
	if vol.accountid:
		return volume_delete(request, vol_id)
	
	if vol and vol.status == "file not found":
		db = EucalyptusDB()
		db.deleteVolume(vol_id)
		vol.status = "deleting"
		request.session.modified = True

	return volume_view(request)

def volume_view(request):

	#メニューを「テンプレート」に設定
	request.session['ss_sys_menu'] = "resource"
	request.session['ss_sys_resource_menu'] = "volume_list"
	#セッションからログインユーザ情報を取得する
	login_user = request.session['ss_usr_user']
	#logger.debug("login user:%s@%s" % (login_user.id, login_user.account_id))

	init_params(request)
	set_params(request)

	# get data
	if isRefresh(request):
		getData(request, login_user)

	if 'selected_account' in request.POST:
		selected_account = request.POST['selected_account']
	else:
		selected_account = "all"

	filtered = filter_vol(request.session['res_volumes'],selected_account)
	volume_list = sort_vol(filtered,request)

	volume_sum = 0
	for vol in volume_list:
		volume_sum += int(vol.size)

	return render_to_response('resource_volume_view.html',
		{'volume_list': volume_list,
		'selected_account':selected_account,
		'volume_sum':volume_sum},
		context_instance=RequestContext(request))

def snapshot_view(request):

	#メニューを「テンプレート」に設定
	request.session['ss_sys_menu'] = "resource"
	request.session['ss_sys_resource_menu'] = "snapshot_list"
	#セッションからログインユーザ情報を取得する
	login_user = request.session['ss_usr_user']

	init_params(request)
	set_params(request)
	#(sorttime, sortacc, sortvol, sortsnap, sortstat) = snap_params(request)
	#logger.debug("extract:%s" % extract)

	# get data
	if isRefresh(request):
		getData(request, login_user)

	if 'selected_account' in request.POST:
		selected_account = request.POST['selected_account']
	else:
		selected_account = "all"

	filtered = filter_snap(request.session['res_snapshots'],selected_account)
	snapshot_list = sort_snap(filtered,request)

	snapshot_sum = 0
	for snap in snapshot_list:
		snapshot_sum += int(snap.size)

	return render_to_response('resource_snapshot_view.html',
		{'snapshot_list': snapshot_list,
		'selected_account':selected_account,
		'snapshot_sum':snapshot_sum},
		context_instance=RequestContext(request))

def filter_properties(raw_list,search_phrase):
	if search_phrase != "":
		filtered_list = []
		for prop in raw_list:
			if search_phrase in prop.name:
				filtered_list.append(prop)
		raw_list = filtered_list
	return raw_list

def properties_view(request):

	#メニューを「テンプレート」に設定
	request.session['ss_sys_menu'] = "resource"
	request.session['ss_sys_resource_menu'] = "property_list"
	#セッションからログインユーザ情報を取得する
	login_user = request.session['ss_usr_user']

	# get data
	if isRefresh(request) or not 'cloud_properties' in request.session:
		tool = GetEucalyptusInfoBy2ool()
		request.session['cloud_properties'] = tool.getCloudProperties(login_user)

	if 'search_phrase' in request.POST:
		search_phrase = request.POST['search_phrase']
	else:
		search_phrase = ""

	property_list = filter_properties(request.session['cloud_properties'],search_phrase)

	return render_to_response('properties_view.html',
		{'property_list': property_list,
		'search_phrase':search_phrase},
		context_instance=RequestContext(request))

