#!/bin/bash
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

BASEDIR=$(cd $(dirname $0); pwd -P)

# DEBUGモード解除
#sed -i -e "s|^\(DEBUG[[:blank:]]*\=[[:blank:]]*\)True$|\1False|" settings.py >/dev/null 2>&1

PORT=16000
# Djangoサーバ起動(ノーハングアップ)
cd ${BASEDIR}
nohup python ${BASEDIR}/manage.py runserver --noreload 0.0.0.0:${PORT} >>stdout.log 2>&1 &

DJANGO_PID=$!
echo ${DJANGO_PID} > django_pid

sleep 5s

PS_LOG=./ps_log.$$
ps -ef | sed 's| \+| |g' | cut -d' ' -f2 >${PS_LOG}

grep ^${DJANGO_PID}$ ${PS_LOG} >/dev/null 2>&1
if [ $? -ne 0 ]; then
  echo "Django could not start."
  rm -f django_pid
fi

rm -f ${PS_LOG}
