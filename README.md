# transfer
数据库迁移
开发背景：
  公司业务系统已经运行多年，运行期间产生了大量历史数据，导致数据库备份、统计更新和重组时间变长，查询数据库性能降低，增加了数据库日常管理成本，同时也消耗了大量高端存储资源，增加了生产运营成本。
为了改善现有问题，本次计划通过建设华泰数据归档自动化平台，先对公司生产运行库中的规则报价数据进行数据归档处理，同时期望通过本次归档项目的实施，为公司最终能沉淀出一个较好的数据归档自动化工作平台，而不是简单通过堆积工作量来完成数据迁移。  
环境准备：
1.两台虚拟机，安装oracle数据库，我使用的是Oracle 11g的版本
开通虚拟机Oracle的访问权限，执行以下三个命令：
  sqlplus / as sysdba
  startup
  lsnrctl start
2.Python3.6  Django1.11.6

