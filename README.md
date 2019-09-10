# transfer
数据库迁移
环境准备：
1.两台虚拟机，安装oracle数据库，我使用的是Oracle 11g的版本
开通虚拟机Oracle的访问权限，执行以下三个命令：
  sqlplus / as sysdba
  startup
  lsnrctl start
2.Python3.6  Django1.11.6
