"""Test internal MARS functions.

Test internal MARS functions.
"""
import beeflow.scheduler.mars as mars
import beeflow.scheduler.sched_types as sched_types


def test_workflow2vec_one_task():
    """Test workflow2vec() with one task.

    Test workflow2vec() with one task.
    """
    tasks = [sched_types.Task(workflow_name='workflow-1', task_name='task-1',
                              requirements={'cost': 3.0, 'max_runtime': 2})]

    vec = mars.workflow2vec(tasks)

    # TODO: Assert correct size and contains task
    assert len(vec) == mars.VECTOR_SIZE
    assert vec[0] == 3.0
    assert vec[1] == 2.0
    assert all(v == 0.0 for v in vec[2:])


def test_workflow2vec_three_tasks():
    """Test workflow2vec() with three tasks.

    Test workflow2vec() with three tasks.
    """
    tasks = [
        sched_types.Task(workflow_name='workflow-1',
                         task_name='task-1',
                         requirements={'cost': 3.0, 'max_runtime': 4}),
        sched_types.Task(workflow_name='workflow-1', task_name='task-2',
                         requirements={'cost': 44.0, 'max_runtime': 1}),
        sched_types.Task(workflow_name='workflow-1', task_name='task-3',
                         requirements={'cost': -10.0, 'max_runtime': 55})
    ]

    vec = mars.workflow2vec(tasks)

    # TODO: Assert correct size and contains task information of all three
    # tasks
    assert len(vec) == mars.VECTOR_SIZE
    assert vec[0] == 3.0
    assert vec[1] == 4.0
    assert vec[2] == 44.0
    assert vec[3] == 1.0
    assert vec[4] == -10.0
    assert vec[5] == 55.0
    assert all(v == 0.0 for v in vec[6:])
    # assert vec == []


# def test_build_availability_list():
#    """Test build_availability_list() with one task and no resources.
#
#    Test build_availability_list() with one task and no resources.
#    """
#    tasks = [sched_types.Task(workflow_name='workflow-1', task_name='task-1',
#                              requirements={'cost': 33.0, 'max_runtime': 44})]
#
#    assert mars.build_availability_list(tasks, tasks[0], []) == []

# TODO: Add more tests for test_build_availability_list()
