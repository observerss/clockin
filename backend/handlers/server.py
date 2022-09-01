from datetime import date

from sqlalchemy import select
from invoke.context import Context

from schemas import DoneClockRequest, AddUserRequest, AddPlanRequest
from models import Session, Record, Clock
from handlers.tasks import add_plan, update_user


def handle_add_plan(req: AddPlanRequest):
    add_plan(
        username=req.username,
        robotname=req.robotname,
        scriptname=req.scriptname,
        userid=req.userid,
    )


def handle_add_user(req: AddUserRequest):
    from hamicli import HamiCli

    cli = HamiCli(cookie=req.cookie, fetch=True)

    # 上一步初始化的东西都拿到了, 直接关闭cli即可
    cli.close()

    update_user(
        cookie=req.cookie,
        user_info=cli.user,
        robots=cli.robots,
        scripts=cli.scripts,
        installations=cli.installations,
    )


def handle_done_clock(req: DoneClockRequest):
    with Session() as session:
        record = Record(
            user_id=req.user_id,
            robot_id=req.robot_id,
            script_id=req.script_id,
            app_env=req.app_env,
            timestamp=req.timestamp,
            extra=req.extra,
        )
        session.add(record)

        statement = (
            select(Clock)
            .where(Clock.user_id == req.user_id)
            .where(Clock.date == date.today())
        )
        clock = session.execute(statement).scalar()
        if not clock:
            clock = Clock(
                user_id=req.user_id,
                date=date.today(),
            )
            session.add(clock)

        direction = req.extra.get("direction")
        done = req.extra.get("done")

        if direction == "in" and done:
            clock.clockin = True
            clock.clokout = False
        elif direction == "out" and done:
            clock.clockout = True

        session.commit()
