from typing import Iterable, List

from sqlalchemy import select, update
from sqlalchemy.orm import joinedload
from models import User, Script, Installation, Robot, Plan, Session, PlanType, engine
from schemas import UserInfo, ScriptInfo, InstallationInfo, RobotInfo
from logger import logger


def update_user(
    cookie: str,
    user_info: UserInfo,
    robots: List[RobotInfo],
    scripts: List[ScriptInfo],
    installations: List[InstallationInfo],
):
    with Session() as session:
        statement = select(User).filter_by(id=user_info.user_id)
        user: User = session.execute(statement).scalar_one_or_none()

        if user:
            for key, value in user_info:
                setattr(user, key, value)
            user.cookie = cookie
        else:
            user_dict = user_info.dict()
            user_dict["id"] = user_dict.pop("user_id")
            user = User(cookie=cookie, **user_dict)
            session.add(user)

        logger.debug("updating user")

        update_robots(session, robots)
        update_scripts(session, scripts)
        update_installations(session, installations)

        session.commit()


def add_plan(
    username: str = "", robotname: str = "", scriptname: str = "", userid: str = ""
):
    user: User
    with Session() as session:
        statement1 = (
            select(User.id, Robot.id, Script.id, Script.configuration)
            .join(User.robots)
            .join(User.scripts)
        )
        statement2 = (
            select(User.id, Robot.id, Installation.id, Installation.configuration)
            .join(User.robots)
            .join(User.installations)
        )

        if username:
            statement1 = statement1.where(User.username == username)
            statement2 = statement2.where(User.username == username)

        if userid:
            statement1 = statement1.where(User.id == userid)
            statement2 = statement2.where(User.id == userid)

        if robotname:
            statement1 = statement1.where(Robot.name == robotname)
            statement2 = statement2.where(Robot.name == robotname)

        if scriptname:
            statement1 = statement1.where(Installation.name == scriptname)
            statement2 = statement2.where(Installation.name == scriptname)

        logger.debug(
            f"statement1: {statement1.compile(engine, compile_kwargs={'literal_binds': True})}"
        )
        logger.debug(
            f"statement2: {statement1.compile(engine, compile_kwargs={'literal_binds': True})}"
        )

        values1 = session.execute(statement1).first()
        values2 = session.execute(statement2).first()
        logger.info(f"script values: {values1}")
        logger.info(f"installation values: {values2}")

        if values1:
            u, r, s, c, t = (
                values1[0],
                values1[1],
                values1[2],
                values1[3],
                PlanType.script,
            )
        elif values2:
            u, r, s, c, t = (
                values2[0],
                values2[1],
                values2[2],
                values1[3],
                PlanType.installation,
            )
        else:
            logger.error(
                f"selection not found: {username}/{robotname}/{scriptname}/{userid}"
            )
            return

        plan = session.execute(
            select(Plan)
            .where(Plan.user_id == u)
            .where(Plan.robot_id == r)
            .where(Plan.script_id == s)
            .where(Plan.type == t)
        ).first()

        if plan:
            plan = plan[0]
            logger.info(f"updating plan: {plan.__dict__}")

        if not plan:
            plan = Plan(
                user_id=u,
                robot_id=r,
                script_id=s,
                type=t,
            )
            session.add(plan)
            logger.info(f"adding plan: {plan.__dict__}")

        ranges = get_ranges_from_configuration(c)
        if ranges:
            plan.ranges = ranges

        session.commit()


def del_plan(id: int):
    with Session() as session:
        statement = update(Plan).where(Plan.id == id).values(deleted=True)
        session.execute(statement)
        session.commit()


def list_plans():
    with Session() as session:
        statement = (
            select(Plan)
            .options(joinedload(Plan.user))
            .options(joinedload(Plan.script))
            .options(joinedload(Plan.script))
            .options(joinedload(Plan.installation))
        )
        plan: Plan
        for plan in session.execute(statement).scalars():
            if plan.type == PlanType.script:
                logger.info(
                    f"{plan.id}, {plan.type}, {plan.user.username}, {plan.robot.name}, {plan.script.name}"
                )
            else:
                logger.info(
                    f"{plan.id}, {plan.type}, {plan.user.username}, {plan.robot.name}, {plan.installation.name}"
                )


def update_robots(session: Session, robots: List[RobotInfo]):
    logger.debug("updating robots")
    statement = (
        update(Robot).where(Robot.id.not_in(iter_ids(robots))).values(deleted=True)
    )
    session.execute(statement)

    updated_ids = set()
    robot: Robot
    statement = select(Robot).where(Robot.id.in_(iter_ids(robots)))
    for robot in session.execute(statement).scalars():
        updated_ids.add(robot.id)
        for ri in robots:
            if ri.id == robot.id:
                for key, value in ri:
                    setattr(robot, key, value)
                break
    for ri in robots:
        if ri.id not in updated_ids:
            session.add(Robot(**ri.dict()))


def update_scripts(session: Session, scripts: List[ScriptInfo]):
    logger.debug("updating scripts")
    statement = (
        update(Script).where(Script.id.not_in(iter_ids(scripts))).values(deleted=True)
    )
    session.execute(statement)

    updated_ids = set()
    script: Script
    statement = select(Script).where(Script.id.in_(iter_ids(scripts)))
    for script in session.execute(statement).scalars():
        updated_ids.add(script.id)
        for si in scripts:
            if si.id == script.id:
                for key, value in si:
                    setattr(script, key, value)
                break
    for si in scripts:
        if si.id not in updated_ids:
            session.add(Script(**si.dict()))


def update_installations(session: Session, installations: List[InstallationInfo]):
    logger.debug("updating installations")
    statement = (
        update(Installation)
        .where(Installation.id.not_in(iter_ids(installations)))
        .values(deleted=True)
    )
    session.execute(statement)

    updated_ids = set()
    installation: Installation
    statement = select(Installation).where(Installation.id.in_(iter_ids(installations)))
    for installation in session.execute(statement).scalars():
        updated_ids.add(installation.id)
        for ii in installations:
            if ii.id == installation.id:
                for key, value in ii:
                    setattr(installation, key, value)
                break
    for ii in installations:
        if ii.id not in updated_ids:
            session.add(Installation(**ii.dict()))


def iter_ids(iterable: Iterable):
    for item in iterable:
        yield item.id


def get_ranges_from_configuration(configuration: dict):
    def get_config(key: str):
        return configuration.get("values", {}).get(key) or configuration.get(
            "defaultValues", {}
        ).get(key)

    clockin_range = get_config("clockInRange")
    clockout_range = get_config("clockOutRange")
    ranges = dict(clockin_range=clockin_range, clockout_range=clockout_range)
    logger.info(f"ranges = {ranges}")
    return ranges
