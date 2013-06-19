/* COPYRIGHT FUJITSU SOCIAL SCIENCE LABORATORY LIMITED 2012
All rights reserved.

Redistribution and use in source and binary forms, with or without modification,
are permitted provided that the following conditions are met:

+ Redistributions of source code must retain the above copyright notice, this list of conditions
and the following disclaimer.
+ Redistributions in binary form must reproduce the above copyright notice, this list of conditions
and the following disclaimer in the documentation and/or other materials provided with the distribution.
+ Neither the name of the FUJITSU SOCIAL SCIENCE LABORATORY LIMITED nor the names of its contributors
may be used to endorse or promote products derived from this software without specific prior written
permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND ANY EXPRESS OR
IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND
FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR
CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY,
WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN
ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE. */

function switchDisplay($buttonInfo){
    //$buttonInfoはjQueryオブジェクトです。
    var isShown;
    isShown = $buttonInfo.parents("table").find(".detail").hasClass("shown");
    if(isShown){;
        $buttonInfo.parents("table").find(".detail").hide();
        $buttonInfo.parents("table").find(".detail").addClass("hidden");
        $buttonInfo.parents("table").find(".detail").removeClass("shown");
        $buttonInfo.text("↓詳細表示");
    }else{
        $buttonInfo.parents("table").find(".detail").show();
        $buttonInfo.parents("table").find(".detail").addClass("shown");
        $buttonInfo.parents("table").find(".detail").removeClass("hidden");
        $buttonInfo.text("↑標準表示");
    }
}

$(document).ready(function(){
    //table偶数行に"even"クラスを付加する。
    //色の指定はスタイルシートにて行う。
    $(".vmachine_info tr:even").addClass("even");

    //////////いまは、色変え＆"＞"の位置替えだけ///////////
    //////////色替えですが一時的にここでやります///
    $("#left_contents .nav li.left_contents_item").click(function(){
        $("#left_contents .nav li.left_contents_item").css("backgroundColor","#ECEFE7");
        $(".menu_selected_text").text("");

        $(this).css("backgroundColor","#ffdf3a");
    });
});

function console_output_window(instance_id){
    url = "/machine/getconsole/" + instance_id　+ "/";
	window.open(url,"window01","width=800,height=600,status=no,scrollbars=yes");
}
