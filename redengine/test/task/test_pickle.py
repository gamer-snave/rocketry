
import pickle
from inspect import isfunction
from textwrap import dedent
import os

import pytest

from redengine.tasks import FuncTask, PyScript
from redengine.conditions import TaskFailed
from redengine.arguments import Arg


def func_on_main_level():
    pass

def pickle_dump_read(obj):
    p = pickle.dumps(obj)
    return pickle.loads(p)

class TestFunc:

    def test_func_on_main(self):
        task = FuncTask(func_on_main_level)
        pick_task = pickle_dump_read(task)
        assert pick_task.func.__name__ == "func_on_main_level"
        assert isfunction(pick_task.func)

    def test_func_nested(self):
        # This cannot be pickled (cannot use execution == process)
        def func_nested():
            pass
        task = FuncTask(func_nested, execution="process", name="unpicklable")
        with pytest.raises(AttributeError):
            pickle_dump_read(task)
        # This should not raise (though still not pickleable)
        task = FuncTask(func_nested, execution="thread", name="picklable")

    def test_unpicklable_start_cond(self):
        def func_nested():
            pass
        unpkl_task = FuncTask(func_nested, execution="thread")
        task = FuncTask(func_on_main_level, execution="process", start_cond=TaskFailed(task=unpkl_task))

        pick_task = pickle_dump_read(task)
        assert pick_task.func.__name__ == "func_on_main_level"
        assert isfunction(pick_task.func)
        assert pick_task.start_cond is None

    def test_unpicklable_end_cond(self):
        def func_nested():
            pass
        unpkl_task = FuncTask(func_nested, execution="thread")
        task = FuncTask(func_on_main_level, execution="process", end_cond=TaskFailed(task=unpkl_task))

        pick_task = pickle_dump_read(task)
        assert pick_task.func.__name__ == "func_on_main_level"
        assert isfunction(pick_task.func)
        assert pick_task.end_cond is None

    def test_unpicklable_session(self, session):
        def func_nested():
            pass
        unpkl_task = FuncTask(func_nested, execution="thread", name="unpicklable")
        task = FuncTask(func_on_main_level, execution="process", name="picklable")

        assert session.tasks == {"unpicklable": unpkl_task, "picklable": task}

        pick_task = pickle_dump_read(task)
        assert pick_task.func.__name__ == "func_on_main_level"
        assert isfunction(pick_task.func)
        assert pick_task.session is not session
        pickle_dump_read(pick_task.session)

    def test_unpicklable_session_params(self, session):
        session.parameters["unpicklable"] = FuncTask(lambda:None, execution="main", name="unpicklable")
        session.parameters["picklable"] = "myval"
        task = FuncTask(func_on_main_level, execution="process", name="picklable")
        pick_task = pickle_dump_read(task)
        
        assert pick_task.session.parameters.to_dict() == {"picklable": "myval"}

class TestScript:

    def test_script_unpicklable(self, tmpdir):
        content = """
        def decor(f):
            def wrapper(*args, **kwargs):
                return f(*args, **kwargs)
            return wrapper

        @decor
        def main():
            pass

        
        """
        script = os.path.join(str(tmpdir), "script.py")
        with open(script, "w") as f:
            f.write(dedent(content))

        task = PyScript(script, func="main")
        # The task should fail in execution
        pkl_task = pickle_dump_read(task)