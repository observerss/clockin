import time
import threading
from typing import List
from concurrent.futures import ThreadPoolExecutor

from config import get_config
from models import Plan
from logger import logger


class Job:
    def __init__(self, plan: Plan):
        self.plan = plan

    def run(self):
        pass


class JobManager:
    def __init__(self):
        pass

    def update(self, plans: List[Plan]):
        pass

    def load_plans(self) -> List[Plan]:
        raise NotImplementedError

    def get_jobs(self):
        """
        获取可以运行的任务
        """
        pass


class Scheduler:
    threads = get_config()["plan"]["threads"]
    interval = get_config()["plan"]["interval"]

    def __init__(self, threads: int) -> None:
        self.executor = ThreadPoolExecutor(self.threads)
        self.jobmanager = JobManager()

    def start(self):
        self.run()

    def run(self):
        while True:
            current_time = time.time()
            try:
                for job in self.jobmanager.get_jobs():
                    self.executor.submit(job.run)
            except Exception as e:
                logger.error(str(e))
            finally:
                time.sleep(max(0, self.interval - (time.time() - current_time)))


scheduler = Scheduler(threads=10)
threading.Thread(target=scheduler.start, daemon=True).start()
