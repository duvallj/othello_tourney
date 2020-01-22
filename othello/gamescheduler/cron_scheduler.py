import asyncio
from contextlib import suppress
import logging as log
from traceback import extract_tb

class CronScheduler():
    def __init__(self, loop, *args, **kwargs):
        self.loop = loop
        super(CronScheduler, self).__init__(*args, **kwargs)

        self.task_list = dict()
        self.task_running = dict()
        self.task_func = dict()
        self.task_wait = dict()

    def schedule_periodic(self, func, args, kwargs, time, taskid):
        self.task_func[taskid] = (func, args, kwargs)
        self.task_wait[taskid] = time
        self.task_running[taskid] = False

    def start_task(self, taskid):
        if taskid in self.task_running and not self.task_running[taskid]:
            self.task_running[taskid] = True
            self.task_list[taskid] = asyncio.ensure_future(self.run_task(taskid), loop=self.loop)

    async def stop_task(self, taskid):
        if taskid in self.task_running and self.task_running[taskid]:
            self.task_running[taskid] = False
            self.task_list[taskid].cancel()
            with suppress(asyncio.CancelledError):
                await self.task_list[taskid]

    async def run_task(self, taskid):
        func, args, kwargs = self.task_func[taskid]
        while True:
            try:
                await func(*args, **kwargs)
            except Exception as e:
                log.warn("error in {}: ".format(taskid) + str(e))
                log.warn("traceback: {}".format(extract_tb(e.__traceback__)))
            await asyncio.sleep(self.task_wait[taskid])
