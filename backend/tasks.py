from invoke import task

from models import Base, engine

from handlers.tasks import (
    update_user as update_user_db,
    add_plan as add_plan_db,
    del_plan as del_plan_db,
    list_plans as list_plans_db,
)
from handlers.plan import start_scheduler


@task
def init_db(c, force=False):
    """初始化数据库"""
    if force:
        Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)


@task
def add_user(c, cookie=""):
    """
    添加用户(By Cookie), 并以此更新用户的连接信息
    """
    from hamicli import HamiCli

    cli = HamiCli(cookie=cookie, fetch=True)

    # 上一步初始化的东西都拿到了, 直接关闭cli即可
    cli.close()

    update_user_db(
        cookie=cookie,
        user_info=cli.user,
        robots=cli.robots,
        scripts=cli.scripts,
        installations=cli.installations,
    )


@task
def update_user(c, cookie=""):
    """
    更新用户Cookie, 并以此更新用户的连接信息
    """
    return add_user(c, cookie)


@task
def list_plans(c):
    """
    列表所有的定时任务
    """
    return list_plans_db()


@task
def add_plan(c, username="", robotname="", scriptname=""):
    """
    添加用户定时任务

    :param username: 用户名称
    :param robotname: 机器人名称
    :param scriptname: 脚本名称
    """
    return add_plan_db(username=username, robotname=robotname, scriptname=scriptname)


@task
def del_plan(c, id=0):
    """
    删除定时任务
    """
    return del_plan_db(id)


@task
def run_plans(c):
    """
    执行定时任务
    """
    thread = start_scheduler()
    thread.join()
