"""
Loom is a small build system in Python.

Loom executes workflows in Asyncio, through lazy evaluation and memoization.
The `Lazy` class contains a `asyncio.lock` and a `Result` object. When multiple
tasks ask for the result of the same dependent task, the lock makes sure a
computation is perforemed only once. Once the lock is free, all future requests
immediately return the memoized result.

  .------.        .------. 
 |  Lazy  | -->  |  Task  |
  `------'        `------' 

  .--------.        .--------. 
 |  LazyDB  | -->  |  TaskDB  |
  `--------'        `--------' 

"""

from .program import Program, resolve_tasks
from .task import Task, TaskDB, Target

__all__ = ["Program", "resolve_tasks", "Task", "TaskDB", "Target"]
