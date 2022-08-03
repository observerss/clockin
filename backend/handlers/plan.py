import time
import threading
from typing import List, Dict, Iterable
from datetime import date, datetime
from concurrent.futures import ThreadPoolExecutor

from logger import logger
from sqlalchemy import select
from sqlalchemy.orm import joinedload

from config import get_config
from schemas import UserInfo
from models import Plan, Clock, Session, PlanType, object_as_dict
from hamicli import HamiCli
from utils import logs_error


class Job:
    def __init__(self, plan: Plan):
        self.plan = plan

    @logs_error
    def run(self):
        plan = self.plan

        if plan.type == PlanType.script:
            script_name = plan.script.name
            script_id = plan.script_id
        else:
            script_name = plan.installation.name
            script_id = plan.script_id

        logger.info(
            f"running job: {plan.user.username}, {script_name}, {plan.robot.name}"
        )

        user_info = UserInfo(
            user_id=plan.user_id,
            **object_as_dict(plan.user),
        )

        cli = HamiCli(user_info=user_info, fetch=False)

        if plan.type == PlanType.script:
            cli.run_script(script_id, plan.robot)
        else:
            cli.run_installation(script_id, plan.robot)

        time.sleep(1)
        cli.close()


class JobManager:
    clockin_range = (8, 18)
    clockout_range = (19, 24)

    def __init__(self):
        self.plans: List[Plan] = []
        self.clocked_dict: Dict[str, Clock] = {}  # user_id => Clock

    def reload_models(self, session: Session):
        self.reload_plans(session)
        self.reload_clocks(session)

    def reload_plans(self, session: Session):
        """刷新生效的定时任务Plans"""
        statement = (
            select(Plan)
            .where(Plan.deleted == False)
            .options(joinedload(Plan.user))
            .options(joinedload(Plan.robot))
        )
        self.plans = session.execute(statement).scalars().all()

    def reload_clocks(self, session: Session):
        """刷新打卡状态"""
        statement = (
            select(Clock)
            .where(Clock.user_id.in_(plan.user_id for plan in self.plans))
            .where(Clock.date == date.today())
        )

        clocks = session.execute(statement).scalars().all()

        self.clocked_dict.clear()

        for clock in clocks:
            self.clocked_dict[clock.user_id] = clock

        # 新建clocks
        for plan in self.plans:
            if plan.user_id not in self.clocked_dict:
                clock = Clock(user_id=plan.user_id, date=date.today())
                self.clocked_dict[plan.user_id] = clock
                session.add(clock)
        session.commit()

    def load_lazy_columns(self, plan: Plan):
        _ = plan.script
        _ = plan.installation

    def parse_range(self, ran: str):
        return ran.split("-")

    def get_jobs(self) -> Iterable[Job]:
        """
        获取可以运行的任务
        """
        with Session() as session:
            self.reload_models(session=session)
            for plan in self.plans:
                clock = self.clocked_dict.get(plan.user_id)
                if clock:
                    now = datetime.now()

                    before_in, after_in = self.parse_range(
                        (plan.ranges or {}).get("clockin_range", "8:00-11:00")
                    )
                    before_out, after_out = self.parse_range(
                        (plan.ranges or {}).get("clockout_range", "19:00-24:00")
                    )

                    if (
                        not clock.clockin
                        and before_in <= now.strftime("%H:%M") < after_in
                    ):
                        self.load_lazy_columns(plan)
                        yield Job(plan=plan)

                    elif (
                        clock.clockin
                        and not clock.clockout
                        and before_out <= now.strftime("%H:%M") < after_out
                    ):
                        self.load_lazy_columns(plan)
                        yield Job(plan=plan)


class Scheduler:
    threads = get_config()["plan"]["threads"]
    interval = get_config()["plan"]["interval"]

    def __init__(self) -> None:
        self.executor = ThreadPoolExecutor(self.threads)
        self.jobmanager = JobManager()

    def start(self):
        self.run()

    def run(self):
        while True:
            current_time = time.time()
            logger.debug("scheduler run")
            try:
                for job in self.jobmanager.get_jobs():
                    self.executor.submit(job.run)
            except Exception as e:
                logger.error(str(e))
            finally:
                time.sleep(max(0, self.interval - (time.time() - current_time)))


scheduler = Scheduler()


def start_scheduler() -> threading.Thread:
    thread = threading.Thread(target=scheduler.start, daemon=True)
    thread.start()
    return thread
