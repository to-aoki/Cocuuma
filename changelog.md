## v1.0 - 2013/06/23
------
���񃊃��[�X

## v1.1 - 2013/09/17
------
����Cocuuma(v1.0)�������p�̏ꍇ��v1.1�̎��Y�ɏ㏑��������ɁA
���̃R�}���h�ɂ�藘�p����DB�X�L�[�}���C�����Ă��������B
```lang
# su - cocuuma
$ cd /var/lib/cocuuma/koala/
$ python manage.py syncdb
```

Features:
  - ���z�T�[�o�y�[�W�̃{�^���̗p����C��
  - �R���\�[���o�� 3.3 �Ή��ibase64�j
  - eucalyptus 3.3�Ή�
  -- eucalyptus/euca2ools�̃o�[�W�����擾
  -- login���̃��N�G�X�gID�I��
  -- describe nodes�̃p�[�X���@
  -- �Ǘ����j���[�ɃC���X�^���X���X�g�擾
  - ���z�T�[�o�y�[�W�����z�T�[�o���ɃC���X�^���XID��\��
  - �f�[�^�{�����[���y�[�W���A�^�b�`�扼�z�}�V���Ƀ}�V������\��
  - ���z�T�[�o�N�����ł��T�[�o�O���[�v�̕ҏW���\��
  - �T�[�o�O���[�v�̉��z�}�V���̍폜���\�Ɂi�e���v���[�g�P�ʂŁj
  - ���z�T�[�o�y�[�W�@�u���̃}�V������e���v���[�g���쐬�v�{�^�������iEBS�u�[�g�C���X�^���X�̂݁j
  - ���z�T�[�o��ʂ����SSH�^�[�~�i���v���O�����̌Ăяo���uSSH���O�C���v�{�^���iIE�̂ݓ���j
