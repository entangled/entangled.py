from __future__ import annotations
import pytest
from dataclasses import dataclass
from typing import Any
from entangled.loom.task import Task, TaskDB
import uuid

@dataclass
class PyFunc(Task[str, Any]):
    foo: Any
    db: TaskDB

    async def run(self):
        args = [self.db.index[t].result for t in self.dependencies]
        return self.foo(*args)

    async def eval(self):
        return await self.db.run(self.targets[0])

@dataclass
class PyLiteral(Task[str, Any]):
    value: Any

    async def run(self):
        return self.value

class PyTaskDB(TaskDB[str, Any]):
    def lazy(self, f):
        def delayed(*args):
            target = uuid.uuid4().hex
            deps = []
            for arg in args:
                if isinstance(arg, Task):
                    deps.append(arg.targets[0])
                else:
                    dep = uuid.uuid4().hex
                    self.add(PyLiteral([dep], [], arg))
                    deps.append(dep)

            task = PyFunc([target], deps, f, self)
            self.add(task)
            return task
        return delayed

@pytest.mark.asyncio
async def test_noodles():
    db = PyTaskDB()

    @db.lazy
    def add1(x, y):
        return x + y

    @db.lazy
    def pure(v):
        return v

    z = add1(pure(3), pure(5))
    await z.eval()
    assert z and z.result == 8

    db.clean()

    exec_order = []
    @db.lazy
    def add2(label, x, y):
        exec_order.append(label)
        return x + y

    x = add2("x", 1, 2)
    y = add2("y", x, 3)
    z = add2("z", x, 4)
    w = add2("w", y, z)
    assert len(exec_order) == 0
    w_result = await w.eval()
    assert w_result.value == 13
    assert exec_order[-1] == "w"
    assert exec_order[0] == "x"

