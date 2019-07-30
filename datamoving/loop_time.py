
import json
from apscheduler.schedulers.background import BackgroundScheduler
from django_apscheduler.jobstores import DjangoJobStore

scheduler = BackgroundScheduler()

try:
    scheduler.add_jobstore(DjangoJobStore())
    scheduler.start()
except(KeyboardInterrupt, SystemExit):
    scheduler.shutdown()


def add_time(func, args, id, timi, start_date):
    # 循环执行，需要几个参数
    # 默认时间格式，days,hours,minutes,seconds
    add = scheduler.add_job(func, 'interval', start_date=start_date, hours=int(timi), args=(args,), id=str(id))
    return add


def test_time(func, args, id):
    # 循环执行，需要几个参数
    # 默认时间格式，days,hours,minutes,seconds
    add = scheduler.add_job(func, 'interval', seconds=30, args=(args,), id=str(id))
    return add


def add_one_time(func, args, id, timi):
    # 年月日，时分秒
    add = scheduler.add_job(func, 'date', args=(args,), run_date=timi, id=str(id))
    return add


def cron_time(func, args, id, timi, start_time):
    timi = json.loads(timi) if type(timi) == str else timi
    print(start_time, 'starting')
    three = start_time.split('T')[1].split(':')
    print(three, 'three')
    if timi['type'] == 'day_of_week':
        if timi['type'] == '':
            timi['days'] = "*"
        add = scheduler.add_job(func, 'cron', args=(args,),
                                day_of_week=timi['days'],
                                month=timi['month'],
                                id=str(id), hour=three[0], minute=three[1], second=three[2], misfire_grace_time=60)
        return add
    elif timi['type'] == 'day' or timi['type'] == 'month':
        if timi['days'] == '':
            timi['days'] = "*"
        add = scheduler.add_job(func, 'cron', args=(args,),
                                day=timi['days'], month=timi['month'],
                                id=str(id), hour=three[0], minute=three[1], second=three[2], misfire_grace_time=60)
                                # id=str(id), hour="*", minute="*", misfire_grace_time=60)
        return add


def get_time(id):
    job = scheduler.get_job(job_id=str(id))

    return job


def rem_time(id):
    job = scheduler.remove_job(job_id=str(id))
    return job


def get_all():
    jobs = scheduler.get_jobs()
    return jobs