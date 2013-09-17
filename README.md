Cocuuma
======================
Cloud on Open-source CUstom Ui vm MAnager  
v.1.1 (2013/9/17)  
Cocuumaはオープンソースクラウド基盤Eucalyptusのクラウドリソース管理機能を提供する日本語フロントエンドです。


ユーザ・ポータル機能
------

+ 仮想マシンの起動
+ 仮想マシンのグループ管理
+ OSイメージのテンプレート管理
+ データボリューム(EBS)の作成・取り付け・バックアップ(snapshot)
+ IPアドレス(elastic IP)の確保・関連付け
+ ssh RSAキー(key pair)管理
+ ファイアウォール（security group）管理
+ 仮想マシンとIPアドレスの紐付け管理
+ 仮想マシンとデータボリュームの紐付け管理
+ zabbixへの仮想マシンの監視設定機能、監視情報参照機能
+ 利用履歴、リソース使用量参照
+ リソース課金（サンプル）計算機能


クラウド・リソース管理機能
------

+ 仮想マシン参照（アカウント別、ノード別）
+ ホストマシン情報（コンポーネント状態、ノードのリソース状態）
+ ホストマシン監視（メモリ、cpu、ディスク使用量）
+ ストレージ領域使用量表示
+ データボリューム管理、残留無効ボリュームの検索と削除

動作環境
------
OS: RedHat/CentOS  
Eucalyptus: 3.0/3.1/3.3  
Apache Http Server 2.2  
Django 1.3.1  
mod_wsgi 3.3  
euca2ools  
eucalyptus-admin-tools  

ライセンス
----------
Copyright &copy; 2013 FUJITSU SOCIAL SCIENCE LABORATORY LIMITED  
Licensed under the 3-clause BSD license  

お問い合わせ先
------
email: cocuuma@googlegroups.com

