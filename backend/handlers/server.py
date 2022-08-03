from datetime import date

from sqlalchemy import select

from schemas import DoneClockRequest
from models import Session, Record, Clock, Script, Installation
from utils import logs_error


@logs_error
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
        elif direction == "out" and done:
            clock.clockout = True

        session.commit()
