
"""Simple Worker class for launching tasks on a system with no workload manager."""

import subprocess

from beeflow.common.worker.worker import Worker
from beeflow.common.crt_interface import ContainerRuntimeInterface
from beeflow.cli import log
import beeflow.common.log as bee_logging
import os

# Import all implemented container runtime drivers now
# No error if they don't exist
try:
    from beeflow.common.crt_drivers import CharliecloudDriver
except ModuleNotFoundError:
    pass
try:
    from beeflow.common.crt_drivers import SingularityDriver
except ModuleNotFoundError:
    pass


class SimpleWorker(Worker):
    """The Worker interface for no workload manager."""

    def __init__(self, container_runtime, **kwargs):
        """Simple worker class."""
        super().__init__(container_runtime=container_runtime, **kwargs)
        # TODO: this should be stored in Redis if possible
        self.tasks = {}

    def submit_task(self, task):
        """Worker submits task; returns job_id, job_state.

        :param task: instance of Task
        :rtype tuple (int, string)
        """
        script = self.build_text(task)
        script_path = os.path.join(self.task_save_path(task), f'{task.name}-{task.id}.sh')
        with open(script_path, 'w') as fp:
            fp.write(script)
        self.tasks[task.id] = subprocess.Popen(['/bin/sh', script_path])
        return (task.id, 'PENDING')

    def cancel_task(self, job_id):
        """Cancel task with job_id; returns job_state.

        :param job_id: to be cancelled
        :type job_id: integer
        :rtype string
        """
        self.tasks[job_id].kill()
        return 'CANCELLED'

    def query_task(self, job_id):
        """Query job state for the task.

        :param job_id: job id to query for status.
        :type job_id: int
        :rtype string
        """
        rc = self.tasks[job_id].poll()
        # XXX: This assumes a standard returncode
        if rc is None:
            return 'RUNNING'
        elif rc == 0:
            return 'COMPLETED'
        else:
            return 'FAILED'
