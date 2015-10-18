# Requirment
* Python
* tornado
* sqlalchemy
* psycopg2

# Database changes

## modify_attence
* 增加modify_attence表，用于记录用户提交的异常考勤处理

## user
* user表增加company、team列，用于记录用户的公司和工作组
* user表增加late_hour列，用于记录用户的缺勤时间
* user表增加off_hour_taken和off_hour_total列，用于记录用户的调休时间
* user表增加is_present字段，用于记录用户的在职、离职状态

## attence

# Attence Logic
* 用户打下班卡的时候就会计算出考勤状态！

# Todo
* 初始化时需要同步数据库信息，把attence中的异常考勤同步到modify_attence中
* 更新user表
* 更新attence表