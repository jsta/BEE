"""Contains the workflow update REST endpoint."""

import os
import json
import shutil
import subprocess
import time
import jsonpickle

from flask import make_response, jsonify
from flask_restful import Resource, reqparse
from beeflow.wf_manager.resources import wf_utils
from beeflow.wf_manager.common import dep_manager
from beeflow.common import log as bee_logging

from beeflow.common.db import wfm_db
from beeflow.common.db.bdb import connect_db


log = bee_logging.setup(__name__)
db_path = wf_utils.get_db_path()


def archive_workflow(db, wf_id):
    """Archive a workflow after completion."""
    # Archive Config
    workflow_dir = wf_utils.get_workflow_dir(wf_id)
    shutil.copyfile(os.path.expanduser("~") + '/.config/beeflow/bee.conf',
                    workflow_dir + '/' + 'bee.conf')

    db.workflows.update_workflow_state(wf_id, 'Archived')
    wf_utils.update_wf_status(wf_id, 'Archived')

    bee_workdir = wf_utils.get_bee_workdir()
    archive_dir = os.path.join(bee_workdir, 'archives')
    os.makedirs(archive_dir, exist_ok=True)
    archive_path = f'../archives/{wf_id}.tgz'
    # We use tar directly since tarfile is apparently very slow
    workflows_dir = wf_utils.get_workflows_dir()
    subprocess.call(['tar', '-czf', archive_path, wf_id], cwd=workflows_dir)


class WFUpdate(Resource):
    """Class to interact with an existing workflow."""

    def __init__(self):
        """Set up arguments."""
        self.reqparse = reqparse.RequestParser()
        self.reqparse.add_argument('wf_id', type=str, location='json',
                                   required=True)
        self.reqparse.add_argument('task_id', type=str, location='json',
                                   required=True)
        self.reqparse.add_argument('job_state', type=str, location='json',
                                   required=True)
        self.reqparse.add_argument('metadata', type=str, location='json',
                                   required=False)
        self.reqparse.add_argument('task_info', type=str, location='json',
                                   required=False)
        self.reqparse.add_argument('output', location='json', required=False)

    def put(self):
        """Update the state of a task from the task manager."""
        db = connect_db(wfm_db, db_path)
        data = self.reqparse.parse_args()
        wf_id = data['wf_id']
        task_id = data['task_id']
        job_state = data['job_state']

        wfi = wf_utils.get_workflow_interface(wf_id)
        task = wfi.get_task_by_id(task_id)
        wfi.set_task_state(task, job_state)
        db.workflows.update_task_state(task_id, wf_id, job_state)

        # Get metadata from update if available
        if 'metadata' in data:
            if data['metadata'] is not None:
                metadata = jsonpickle.decode(data['metadata'])
                wfi.set_task_metadata(task, metadata)

        bee_workdir = wf_utils.get_bee_workdir()
        # Get output from the task
        if 'metadata' in data:
            if data['metadata'] is not None:
                metadata = jsonpickle.decode(data['metadata'])
                old_metadata = wfi.get_task_metadata(task)
                old_metadata.update(metadata)
                wfi.set_task_metadata(task, old_metadata)

        if 'output' in data and data['output'] is not None:
            fname = f'{wfi.workflow_id}_{task.id}_{int(time.time())}.json'
            task_output_path = os.path.join(bee_workdir, fname)
            with open(task_output_path, 'w', encoding='utf8') as fp:
                json.dump(json.loads(data['output']), fp, indent=4)

        if 'task_info' in data and data['task_info'] is not None:
            task_info = jsonpickle.decode(data['task_info'])
            checkpoint_file = task_info['checkpoint_file']
            new_task = wfi.restart_task(task, checkpoint_file)
            if new_task is None:
                log.info('No more restarts')
                wf_state = wfi.get_workflow_state()
                wf_utils.update_wf_status(wf_id, 'Failed')
                db.workflows.update_workflow_state(wf_id, 'Failed')
                return make_response(jsonify(status=f'Task {task_id} set to {job_state}'))
            db.workflows.add_task(new_task.id, wf_id, new_task.name, "WAITING")
            # Submit the restart task
            tasks = [new_task]
            wf_utils.schedule_submit_tasks(wf_id, tasks)
            return make_response(jsonify(status='Task {task_id} restarted'))

        if job_state in ('COMPLETED', 'FAILED'):
            for output in task.outputs:
                if output.glob is not None:
                    wfi.set_task_output(task, output.id, output.glob)
                else:
                    wfi.set_task_output(task, output.id, "temp")
            tasks = wfi.finalize_task(task)
            wf_state = wfi.get_workflow_state()
            if tasks and wf_state != 'PAUSED':
                wf_utils.schedule_submit_tasks(wf_id, tasks)

            if wfi.workflow_completed():
                log.info("Workflow Completed")
                wf_id = wfi.workflow_id
                archive_workflow(db, wf_id)
                pid = db.workflows.get_gdb_pid(wf_id)
                dep_manager.kill_gdb(pid)
            if wf_state == 'FAILED':
                log.info("Workflow failed")
                log.info("Shutting down GDB")
                wf_id = wfi.workflow_id
                archive_workflow(db, wf_id)
                pid = db.workflows.get_gdb_pid(wf_id)
                dep_manager.kill_gdb(pid)

        resp = make_response(jsonify(status=(f'Task {task_id} belonging to WF {wf_id} set to'
                                             f'{job_state}')), 200)
        return resp
# Ignoring C901,R0915: "'WFUPdate.put' is too complex" - this requires a refactor
#                      (or maybe the LOC limit is too low)
# pylama:ignore=C901,R0915
