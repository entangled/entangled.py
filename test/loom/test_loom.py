import pytest
from entangled.loom.task import TaskDB
from entangled.loom.rule import LoomTask, Target
from entangled.filedb import stat

class FileTaskDB(TaskDB[Target, None]):
    pass
