
from powerbase.core.task import Task, register_task_cls
from powerbase.core.exceptions import SchedulerRestart, SchedulerExit

@register_task_cls
class Restart(Task):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.execution = "main"

    def execute_action(self, **kwargs):
        raise SchedulerRestart()

    def get_default_name(self):
        return "restart"

@register_task_cls
class ShutDown(Task):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.execution = "main"

    def execute_action(self, **kwargs):
        raise SchedulerExit()

    def get_default_name(self):
        return "shutdown"