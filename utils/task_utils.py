from datetime import datetime

from models import db, Task


def new_or_update_task(total_num, task_name):
    # 开始更新任务
    task = db.session.query(Task).filter(Task.name == task_name).first()
    today = datetime.now()
    if task is None:
        task = Task()
        task.name = task_name
        task.total_num = total_num
        task.current_num = 0
        task.status = 0  # 执行中
        task.modify_date = today
        task.create_date = today
        db.session.add(task)
    else:
        if task.status == 1 and task.modify_date.strftime("%Y-%m-%d") == today.strftime("%Y-%m-%d"):
            print("today's task is finish")
            return -1  # 任务处理完成, 直接退出
        elif task.modify_date.strftime("%Y-%m-%d") == today.strftime("%Y-%m-%d"):  # 今天的任务
            # 最后的更新时间与当前时间相差较大(3分钟), 说明任务已经被中断, 重启一下任务
            if (datetime.now() - task.modify_date).total_seconds() > 60*3:
                print("today's task is restart")
                task.modify_date = today
                task.total_num = total_num
                task.status = 0  # 执行中
                task.current_num = 0
            else:
                print("today's task is still in progress")
                return task, -1  # 退出
        else:  # 以前的任务, 直接覆盖更新
            task.modify_date = today
            task.total_num = total_num
            task.status = 0  # 执行中
            task.current_num = 0
    db.session.commit()  # 为了后面能看到任务数据
    return task, 1


def process_task_when_normal(task, num=1):
    if task not in db.session:
        db.session.merge(task)

    if task in db.session:
        task.increment(num)
        db.session.commit()  # 把task信息更新到db, 以便轮询能看到
    else:
        print("task is not bond to a session")


def process_task_when_error(task, err_msg):
    task.error(err_msg)
    db.session.commit()

def process_task_when_finish(task, msg):
    task.success(msg)
    db.session.commit()