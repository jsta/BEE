"""Code implementing various scheduling algorithms.

Code implementing scheduling algorithms, such as FCFS, Backfill, etc.
"""

import abc
import time

import beeflow.scheduler.resource_allocation as resource_allocation
import beeflow.scheduler.sched_types as sched_types
import beeflow.scheduler.util as util
import beeflow.scheduler.mars_util as mars_util


class Algorithm(abc.ABC):
    """Scheduling algorithm abstract class.

    Base abstract class for implementing a scheduling algorithm.
    """

    @abc.abstractmethod
    def __init__(self, **kwargs):
        """Scheduling constructor.

        """

    @abc.abstractmethod
    def schedule_all(self, tasks, resources, **kwargs):
        """Schedule all tasks with the implemented algorithm.

        Schedule all tasks with the implemented algorithm.
        :param tasks: list of tasks to schedule
        :type tasks: list of instance of Task
        :param resources: list of resources
        :type resources: list of instance of sched_types.Resource
        """


class SJF(Algorithm):
    """Shortest job first algorithm.

    Class holding scheduling code for runing the shortest job first algorithm.
    """

    def __init__(self, **kwargs):
        """Scheduling constructor.

        """

    @staticmethod
    def schedule_all(tasks, resources, **kwargs):
        """Schedule a list of independent tasks with SJF.

        Schedule a list of independent tasks with SFJ.
        :param tasks: list of tasks to schedule
        :type tasks: list of instance of Task
        :param resources: list of resources
        :type resources list of instance of sched_types.Resource
        """
        # First sort the tasks by how long they are, then send them off to
        # FCFS
        tasks = tasks[:]
        tasks.sort(key=lambda task: task.requirements.max_runtime)
        FCFS.schedule_all(tasks, resources, **kwargs)


class FCFS(Algorithm):
    """FCFS scheduling algorithm.

    This class holds the scheduling code used for the FCFS
    scheduling algorithm.
    """

    def __init__(self, **kwargs):
        """Scheduling constructor.

        """

    @staticmethod
    def schedule_all(tasks, resources, **kwargs):
        """Schedule a list of independent tasks with FCFS.

        Schedule an entire list of tasks using FCFS. Tasks that
        cannot be allocated will be left with an empty allocations
        property.
        :param tasks: list of tasks to schedule
        :type tasks: list of instance of Task
        :param resources: list of resources
        :type resources: list of instance of sched_types.Resource
        """
        allocator = resource_allocation.TaskAllocator(resources)
        start_time = 0
        for task in tasks:
            if not allocator.fits_requirements(task.requirements):
                continue
            # Find the start_time
            while not allocator.can_run_now(task.requirements, start_time):
                start_time = allocator.get_next_end_time(start_time)
            task.allocations = allocator.allocate(task.requirements,
                                                  start_time)


class Backfill(Algorithm):
    """Backfill scheduling algorithm.

    This class holds the scheduling code used for the Backfill
    scheduling algorithm.
    """

    def __init__(self, **kwargs):
        """Scheduling constructor.

        """

    @staticmethod
    def schedule_all(tasks, resources, **kwargs):
        """Schedule a list of independent tasks with Backfill.

        Schedule an entire list of tasks using Backfill. Tasks that
        cannot be allocated will be left with an empty allocations
        property.
        :param tasks: list of tasks to schedule
        :type tasks: list of instance of Task
        :param resources: list of resources
        :type resources: list of instance of sched_types.Resource
        """
        tasks = tasks[:]
        current_time = 0
        allocator = resource_allocation.TaskAllocator(resources)
        while tasks:
            task = tasks.pop(0)
            # Can this task run at all?
            if not allocator.fits_requirements(task.requirements):
                continue
            # Can this task run immediately?
            start_time = current_time
            # max_runtime = task.requirements.max_runtime
            if allocator.can_run_now(task.requirements, start_time):
                allocs = allocator.allocate(task.requirements, start_time)
                task.allocations = allocs
                continue
            # This job must run later, so we need to find the shadow time
            # (earliest time at which the job can run)
            times = allocator.get_end_times()
            times.sort()
            shadow_time = 0
            for time in times:
                if allocator.can_run_now(task.requirements, time):
                    shadow_time = time
                    allocs = allocator.allocate(task.requirements, shadow_time)
                    task.allocations = allocs
                    break
            # Now backfill other tasks
            times.insert(0, current_time)
            remaining = []
            for backfill_task in tasks:
                max_runtime = backfill_task.requirements.max_runtime
                possible_times = [time for time in times
                                  if (time + max_runtime) < shadow_time]
                for time in possible_times:
                    if allocator.can_run_now(backfill_task.requirements, time):
                        allocs = allocator.allocate(backfill_task.requirements,
                                                    time)
                        backfill_task.allocations = allocs
                # Could not backfill this task
                if not backfill_task.allocations:
                    remaining.append(backfill_task)
            # Tasks in remaining cannot be backfilled and must be run later
            # Reset the tasks to the remaining list
            tasks = remaining


class MARS(Algorithm):
    """MARS Scheduler.

    MARS Scheduler.
    """

    def __init__(self, mars_model='model', **kwargs):
        """MARS scheduling constructor.

        :param mars_model: model file path
        :type mars_model: str
        """
        # Only import the mars module if necessary
        import beeflow.scheduler.mars as mars
        self.mod = mars
        self.actor, self.critic = mars.load_models(mars_model)

    def policy(self, actor, critic, task, tasks, possible_allocs):
        """Evaluate the policy function to find scheduling of task.

        Evaluate the policy function with the model task.
        :param actor: actor used for scheduling
        :type actor: instance of mars.ActorModel
        :param critic: critic used during training
        :type critic: instance of mars.CriticModel
        :param task: task to get the scheduling policy for
        :type task: instance of Task
        :param possible_allocs: possible allocations for the task
        :type possible_allocs: list of instance of Allocation
        :rtype: int, index of allocation to use
        """
        mars = self.mod
        # No possible allocations
        if not possible_allocs:
            return -1
        # Convert the task and possible_allocs into a vector
        # for input into the policy function.
        # TODO: Input should include the specific task
        vec = mars_util.workflow2vec(task, tasks)
        vec = mars.tf.constant([vec])
        # Convert the result into an action index
        pl = [float(n) for n in actor.call(vec)[0]]
        a = pl.index(max(pl))
        a = (float(a) / len(pl)) * (len(possible_allocs) - 1)
        return int(a)

    def schedule_all(self, tasks, resources, mars_model='model', **kwargs):
        """Schedule a list of tasks on the given resources.

        Schedule a full list of tasks on the given resources. Note: MARS.load()
        must have been called previously.
        :param tasks: list of tasks to schedule
        :type tasks: list of instance of Task
        :param resources: list of resources
        :type resources: list of instance of Resource
        :param mars_model: the mars model path
        :type mars_model: str
        """
        """
        allocator = resource_allocation.TaskAllocator(resources)
        # TODO: Make policy decisions based on end times, rather than building
        # a possible allocation list
        for task in tasks:
            possible_allocs = allocator.build_allocation_list(task, tasks,
                                                              resources)
            pi = self.policy(self.actor, self.critic, task, tasks,
                             possible_allocs)
            if pi != -1:
                # TODO: This is incorrect
                allocs = possible_allocs[pi]
                allocations.extend(allocs)
                task.allocations = allocs
        """
        # TODO: Rewrite this function using resource_allocation.TaskAllocator()


        # TODO: Set the path somewhere else
        # actor, critic = mars.load_models(mars_model)
        allocations = []
        for task in tasks:
            possible_allocs = build_allocation_list(task, tasks, resources,
                                                    curr_allocs=allocations)
            pi = self.policy(self.actor, self.critic, task, tasks,
                             possible_allocs)
            # -1 indicates no allocation found
            if pi != -1:
                allocs = possible_allocs[pi]
                allocations.extend(allocs)
                task.allocations = allocs
        # TODO: Update time based on runtime of algorithm


class AlgorithmWrapper:
    """Algorithm wrapper class.

    Algorithm wrapper class to be used as a wrap to log the task scheduling
    data for future training and other extra information.
    """

    def __init__(self, cls, alloc_logfile='schedule_log.txt', **kwargs):
        """Algorithm wrapper class constructor.

        Algorithm wrapper class constructor.
        :param cls: object to pass operations onto
        :type cls: algorithm object
        :param alloc_logfile: name of logfile to write task scheduling to
        :type alloc_logfile: str
        :param kwargs: key word arguments to pass to schedule_all()
        :type kwargs: instance of dict
        """
        self.cls = cls
        self.alloc_logfile = alloc_logfile
        self.kwargs = kwargs

    def schedule_all(self, tasks, resources):
        """Schedule all tasks using the internal class and log results.

        Schedule all of the tasks with the internal class and write the
        results out to a log file.
        """
        self.cls.schedule_all(tasks, resources, **self.kwargs)
        with open(self.alloc_logfile, 'a') as fp:
            print('; Log start at', time.time(), file=fp)
            curr_allocs = []
            for task in tasks:
                possible_allocs = build_allocation_list(task, tasks, resources,
                                                        curr_allocs)
                # Find the value of a - the index of the allocation for this
                # task
                a = -1
                # TODO: Calculation of a needs to change
                if task.allocations:
                    start_time = task.allocations[0].start_time
                    # a should be the first alloc with the same start_time
                    for i, alloc in enumerate(possible_allocs):
                        if alloc[0].start_time == start_time:
                            a = i
                            break
                # Output in SWF format
                # TODO: These variables may not be all in the right spot and
                # some may be missing as well
                print(-1, -1, -1, task.requirements.max_runtime,
                      task.requirements.nodes, task.requirements.max_runtime,
                      task.requirements.mem_per_node, task.requirements.nodes, -1,
                      task.requirements.mem_per_node, task.requirements.mem_per_node, -1,
                      #task.requirements.mem, task.requirements.nodes, -1,
                      #task.requirements.mem, task.requirements.mem, -1,
                      -1, -1, -1, -1, -1, -1, -1, file=fp)
                # print(*vec, file=fp)
                curr_allocs.extend(task.allocations)


# TODO: This function and all references to it needs be removed and or updated
# to use the resource_allocation interfacee
def build_allocation_list(task, tasks, resources, curr_allocs):
    """Build a list of allocations for a task.

    :param task: task being allocated
    :type task: instance of sched_types.Task
    :param tasks: list of other tasks
    :type tasks: list of instance of sched_types.Task
    :param resources: list of resources
    :type resources: list of instance of sched_types.Resource
    """
    times = set(t.allocations[0].start_time + t.requirements.max_runtime
                for t in tasks if t.allocations)
    times = list(times)
    # Add initial start time
    times.append(0)
    times.sort()
    allocations = []
    for start_time in times:
        overlap = util.calculate_overlap(curr_allocs, start_time,
                                         task.requirements.max_runtime)
        remaining = sched_types.diff(sched_types.rsum(*resources),
                                     sched_types.rsum(*overlap))
        if remaining.fits_requirements(task.requirements):
            # TODO: Ensure that these allocations are not final (in other
            # other words, if the algorithm decides to pick one and not the
            # other, later on, we don't want there to be conflicts)
            allocs = util.allocate_aggregate(resources, overlap, task,
                                             start_time)
            allocations.append(allocs)
    return allocations


# TODO: Perhaps this value should be a config value
MEDIAN = 2


algorithm_objects = {
    'fcfs': None,
    'mars': None,
    'backfill': None,
    'sjf': None,
}


def load(use_mars=False, algorithm=None, **kwargs):
    """Load data needed by the algorithms.

    Load data needed by algorithms, if necessary.
    """
    algorithm_objects['fcfs'] = FCFS(**kwargs)
    use_mars = use_mars == 'True' or use_mars is True
    if use_mars or algorithm == 'mars':
        print('Loading MARS')
        algorithm_objects['mars'] = MARS(**kwargs)
        # MARS.load(**kwargs)
    algorithm_objects['backfill'] = Backfill(**kwargs)
    algorithm_objects['sjf'] = SJF(**kwargs)


def choose(tasks, use_mars=False, algorithm=None, mars_task_cnt=MEDIAN,
           default_algorithm=None, **kwargs):
    """Choose which algorithm to run at this point.

    Determine which algorithm class needs to run and return it.
    :param tasks: list of tasks:
    :type tasks: list of instance of Task
    :rtype: class derived from Algorithm (not an instance)
    """
    # TODO: Correctly choose based on size of the workflow
    # return Logger(Backfill)
    # Choose the default algorithm 
    default = default_algorithm if default_algorithm is not None else 'fcfs'
    cls = algorithm_objects[default]
    if algorithm is not None:
        cls = algorithm_objects[algorithm]
    if use_mars and len(tasks) >= int(mars_task_cnt):
        cls = algorithm_objects['mars']

    return AlgorithmWrapper(cls, **kwargs)
