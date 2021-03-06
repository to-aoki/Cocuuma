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

function show_keys(btn){

    if (btn.value == "表示") {
        $('.key').removeAttr("style");
    } else {
        $('.key').attr("style","visibility:hidden;");
    }
    btn.value = ((btn.value == "表示" ? "非表示" : "表示"));
}

$(document).ready(function(){

    //////////いまは、色変え＆"＞"の位置替えだけ///////////
    //////////manuの色替えですが一時的にここでやります///
    $(".nav li").click(function(){
        $(".nav li").css("backgroundColor","#ECEFE7");
        $(".menu_selected_text").text("");

        $(this).css("backgroundColor","#E0FFFF");
        $(this).find(".menu_selected_text").text(">");

    });

    //table偶数行に"even"クラスを付加する。
    //色の指定はスタイルシートにて行う。
    $(".template_info tr:even").addClass("even");

    ///紙芝居用///
    $("#menu_template").click(function(){
        location.href="template_list.html";
    });
});