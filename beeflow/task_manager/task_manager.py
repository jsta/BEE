"""Task Manager submits & manages tasks from Work Flow Manager.

Submits, cancels and monitors states of tasks.
Communicates status to the Work Flow Manager, through RESTful API.
"""
from configparser import NoOptionError
import atexit
import sys
import os
import platform
import logging
import jsonpickle
import requests

from flask import Flask, jsonify, make_response
from flask_restful import Resource, Api, reqparse

from apscheduler.schedulers.background import BackgroundScheduler
from beeflow.common.config.config_driver import BeeConfig

try:
    bc = BeeConfig(userconfig=sys.argv[1])
except IndexError:
    bc = BeeConfig()

supported_runtimes = ['Charliecloud', 'Singularity']

# Set Task Manager default port, attempt to prevent collisions
tm_port = 5050
if platform.system() == 'Windows':
    # Get parent's pid to offset ports. uid method better but not available in Windows
    tm_port += os.getppid() % 100
else:
    tm_port += os.getuid() % 100

if bc.userconfig.has_section('task_manager'):
    try:
        bc.userconfig.get('task_manager', 'listen_port')
    except NoOptionError:
        bc.modify_section('user', 'task_manager', {'listen_port': tm_port})
    try:
        bc.userconfig.get('task_manager', 'container_runtime')
    except NoOptionError:
        bc.modify_section('user', 'task_manager', {'container_runtime': 'Charliecloud'})

    if bc.userconfig.get('task_manager', 'container_runtime') not in supported_runtimes:
        sys.exit("Container Runtime not supported! Please check " +
                 str(bc.userconfig_file) + " and restart TaskManager")
else:
    print("[task_manager] section not found in configuration file, default values added")
    tm_listen_port = tm_port
    tm_dict = {'listen_port': tm_listen_port, 'container_runtime': 'Charliecloud'}
    bc.modify_section('user', 'task_manager', tm_dict)


tm_listen_port = bc.userconfig.get('task_manager', 'listen_port')

# Check Workflow manager port
if bc.userconfig.has_section('workflow_manager'):
    try:
        bc.userconfig.get('workflow_manager', 'listen_port')
    except NoOptionError:
        sys.exit("[workflow_manager] missing listen_port in " + str(bc.userconfig_file))
else:
    sys.exit("[workflow_manager] section missing in " + str(bc.userconfig_file))

wfm_listen_port = bc.userconfig.get('workflow_manager', 'listen_port')

flask_app = Flask(__name__)
api = Api(flask_app)

submit_queue = []  # tasks ready to be submitted
job_queue = []  # jobs that are being monitored


def _url():
    """ Returns the url to the WFM. """
    workflow_manager = 'bee_wfm/v1/jobs/'
    return f'http://127.0.0.1:{wfm_listen_port}/{workflow_manager}'


def _resource(tag=""):
    """ Used to access the WFM. """
    return _url() + str(tag)


def update_task_state(task_id, job_state):
    """ Informs the task manager of the current state of a task. """
    resp = requests.put(_resource("update/"),
                        json={'task_id': task_id, 'job_state': job_state})
    if resp.status_code != requests.codes.okay:
        print("WFM not responding")
    else:
        print('Updated task!')


def submit_jobs():
    """ Submits all jobs currently in submit queue to slurm. """
    while len(submit_queue) >= 1:
        # Single value dictionary
        temp = submit_queue.pop(0)
        task_id = list(temp)[0]
        task = temp[task_id]
        job_id, job_state = worker.submit_task(task)

        if job_id == -1:
            # Set job state to failed message
            job_state = 'SUBMIT_FAIL'
        else:
            # place job in queue to monitor and send initial state to WFM
            print(f'Job Submitted: job_id: {job_id} job_state: {job_state}')
            job_queue.append({task_id: {'name': task.name,
                                        'job_id': job_id,
                                        'job_state': job_state}})
        # Send the initial state to WFM
        update_task_state(task_id, job_state)


def update_jobs():
    """ Check and update states of jobs in queue, remove completed jobs. """
    for job in job_queue:
        task_id = list(job)[0]
        current_task = job[task_id]
        job_id = current_task['job_id']
        state = worker.query_task(job_id)
        if state[0] == 1:
            job_state = state[1]
        else:
            job_state = 'ZOMBIE'
        if job_state != current_task['job_state']:
            print(f'{current_task["name"]} {current_task["job_state"]} -> {job_state}')
            current_task['job_state'] = job_state
            update_task_state(task_id, job_state)
        if job_state in ('COMPLETED', 'CANCELLED', 'ZOMBIE'):
            # Remove from the job queue. Our job is finished
            job_queue.remove(job)


def check_tasks():
    """ Looks for newly submitted jobs and updates status of scheduled jobs. """
    submit_jobs()
    update_jobs()


# TODO Decide on the time interval for the scheduler
scheduler = BackgroundScheduler({'apscheduler.timezone': 'UTC'})
scheduler.add_job(func=check_tasks, trigger="interval", seconds=5)
scheduler.start()

# This kills the scheduler when the process terminates
# so we don't accidentally leave a zombie process
atexit.register(lambda: scheduler.shutdown())


class TaskSubmit(Resource):
    """ WFM sends task to the task manager. """
    def __init__(self):
        self.reqparse = reqparse.RequestParser()
        self.reqparse.add_argument('task', type=str, location='json')

    def post(self):
        """ Receives task from WFM. """
        data = self.reqparse.parse_args()
        task = jsonpickle.decode(data['task'])
        submit_queue.append({task.id: task})
        print(f"Added {task.name} to the submit queue")
        resp = make_response(jsonify(msg='Task Added!', status='ok'), 200)
        return resp


class TaskActions(Resource):
    """Actions to take for tasks. """

    def delete(self):
        """ Cancel received from WFM to cancel job, update queue to monitor state."""

        cancel_msg = ""

        for job in job_queue:
            task_id = list(job.keys())[0]
            job_id = job[task_id]['job_id']
            name = job[task_id]['name']

            job_queue.remove(job)
            print(f"Cancelling {name} with job_id: {job_id}")
            success, job_state = worker.cancel_task(job_id)
            cancel_msg += f"{name} {task_id} {success} {job_id} {job_state}"

        resp = make_response(jsonify(msg=cancel_msg, status='ok'), 200)
        return resp

# Slumrworker imported now to make sure configuration is correct. Don't move!
from beeflow.common.worker.worker_interface import WorkerInterface
from beeflow.common.worker.slurm_worker import SlurmWorker
worker = WorkerInterface(SlurmWorker,
                         slurm_socket=bc.userconfig.get('slurmrestd', 'slurm_socket'))

api.add_resource(TaskSubmit, '/bee_tm/v1/task/submit/')
api.add_resource(TaskActions, '/bee_tm/v1/task/')


if __name__ == '__main__':
     # Get the paramater for logging
    try:
        bc.userconfig.get('task_manager', 'log')
    except NoOptionError:
        bc.modify_section('user', 'task_manager',
                          {'log':'/'.join([bc.userconfig['DEFAULT'].get('bee_workdir'),
                                           'logs', 'tm.log'])})
    finally:
        tm_log = bc.userconfig.get('task_manager', 'log')
        tm_log = bc.resolve_path(tm_log)
    print('tm_listen_port:', tm_listen_port)
    print('container_runtime',
          bc.userconfig.get('task_manager', 'container_runtime'))

    handler = logging.FileHandler(tm_log)
    handler.setLevel(logging.DEBUG)

    # Werkzeug logging
    werk_log = logging.getLogger('werkzeug')
    werk_log.setLevel(logging.INFO)
    werk_log.addHandler(handler)

    # Flask logging
    flask_app.logger.addHandler(handler)
    flask_app.run(debug=True, port=str(tm_listen_port))
