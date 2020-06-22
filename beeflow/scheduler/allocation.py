#!/usr/bin/env python3
"""Allocation and scheduling algorithm code."""
import math


class ResourceBase:
    """Resource base.

    Base class with encode() and decode() methods for converting
    objects to basic objects.
    """

    def encode(self):
        """Encode an object and return the basic type.

        Encodes the object and returns a basic type that can be
        converted to JSON or YAML.
        """
        # TODO

    @staticmethod
    def decode(data):
        """Decode a basic type and return the object it represents.

        Decodes basic Python types and returns a newly constructed
        object.
        """
        # TODO


class TimeSlot(ResourceBase):
    """Time slot class.

    A class representing an allocated time slot.
    """

    def __init__(self, start_time, task=None, runtime=0, partition=None):
        """Time slot constructor.

        Initializes a new time slot.
        """
        self.task = task
        self.start_time = start_time
        self.runtime = runtime
        if task is not None:
            self.runtime = task.runtime
        self.partition = partition

    @property
    def open(self):
        """Property that is true when this time slot is open."""
        return self.task is None

    def fits(self, task, min_start_time):
        """Return true if the task fits in this time slot.

        :param task: a task
        :type task: instance of task
        :param min_start_time: minimum starting time
        :type min_start_time: int
        :rtype: bool
        """
        return (self.open and (self.start_time + self.runtime) >= (min_start_time + task.runtime)
                and task.runtime <= self.runtime)

    def encode(self):
        """Encode an object and return the basic type.

        Encodes the object and returns a basic type that can be
        converted to JSON or YAML.
        """
        val = dict(self.__dict__)
        if self.task is not None:
            val['task'] = self.task.encode()
        if self.partition is not None:
            val['partition'] = self.partition.encode()
        return val

    @staticmethod
    def decode(data):
        """Decode a basic type and return the object it represents.

        Decodes basic Python types and returns a newly constructed
        object.
        """
        val = dict(data)
        if 'task' in val:
            val['task'] = Task.decode(val['task'])
        return TimeSlot(**val)
        # return TimeSlot(data['start_time'], task=Task.from_json(data['task']), runtime=task['runtime'])


class Cluster(ResourceBase):
    """Cluster class.

    Class representing an entire cluster, partitions, nodes and resources.
    """

    # TODO
    def __init__(self, name, partitions=[]):
        """Allocation constructor.

        Initialize a new Allocation .
        :param name: name of the cluster
        :type name: str
        """
        self.name = name
        self.partitions = partitions

    def insert_partition(self, partition):
        """Insert a new partition.

        Add a new partition to the current partitions in the cluster.
        :param partition: partition to add
        :type partition: instance of Partition
        """
        self.partitions.append(partition)

    def encode(self):
        """Encode an object and return the basic type.

        Encodes the object and returns a basic type that can be
        converted to JSON or YAML.
        """
        val = dict(self.__dict__)
        for i, p in enumerate(val['partitions']):
            val['partitions'][i] = p.encode()
        return val

    @staticmethod
    def decode(data):
        """Decode a basic type and return the object it represents.

        Decodes basic Python types and returns a newly constructed
        object.
        """
        val = dict(data)
        # or i, p in enumerate(val['partitions']):
        val['partitions'] = [Partition.decode(p) for p in val['partitions']]
        return Cluster(**val)


class Partition(ResourceBase):
    """Partition class.

    Class representing a single partition within a larger cluster.
    """

    def __init__(self, name, slots=[]):
        """Partition constructor.

        Initialize a new partition .
        """
        self.name = name
        self.slots = []

    @property
    def total_time(self):
        """Get the total used time of the partition slots.

        Returns a sum of all the time used by the partition slots.
        """
        return sum(slot.runtime for slot in self.slots)

    def insert(self, task, start_time=0):
        """Insert a task into the partition in a specifc time slot.

        This will insert a new task, cutting up empty time slots
        if necessary. Assumes that the task can fit in this partition
        at the passed start_time without any overlaps.
        """
        # Find where to insert the slot at
        index = None
        t = 0
        for i, slot in enumerate(self.slots):
            if t >= start_time and slot.open:
                # TODO: Perhaps enforce setting correct times
                # Assumes that the slot is big enough
                start_time = t
                index = i
                break
            t += slot.runtime
        if index is not None:
            old_slot = self.slots[index]
            del self.slots[index]
            if old_slot.start_time < start_time:
                self.slots.insert(index, TimeSlot(runtime=start_time-old_slot.start_time,
                                                  start_time=old_slot.start_time, partition=self))
                index += 1
            slot = TimeSlot(task=task, start_time=start_time, partition=self)
            self.slots.insert(index, slot)
            index += 1
            runtime_left = (old_slot.start_time + old_slot.runtime) - (start_time + task.runtime)
            if runtime_left > 0:
                self.slots.insert(index, TimeSlot(start_time=start_time+task.runtime,
                                                  runtime=runtime_left, partition=self))
        else:
            total_time = self.total_time
            if start_time > total_time:
                self.slots.append(TimeSlot(start_time=total_time, runtime=start_time - total_time,
                                           partition=self))
            slot = TimeSlot(task=task, start_time=start_time, partition=self)
            self.slots.append(slot)
        return slot

    def fit(self, task, start_time=0):
        """Fit a task into the partition at the earliest possible time.

        :param task:
        :param start_time:
        :rtype: int
        """
        # TODO: This calculation may be off
        for slot in self.slots:
            if slot.open and (slot.start_time + slot.runtime) >= (start_time + task.runtime):
                return start_time if slot.start_time < start_time else slot.start_time
        # Didn't find an empty slot
        return start_time if self.total_time < start_time else self.total_time

    def encode(self):
        """Encode an object and return the basic type.

        Encodes the object and returns a basic type that can be
        converted to JSON or YAML.
        """
        val = dict(self.__dict__)
        val['slots'] = [slot.encode() for slot in val['slots']]
        return val

    @staticmethod
    def decode(data):
        """Decode a basic type and return the object it represents.

        Decodes basic Python types and returns a newly constructed
        object.
        """
        data = dict(data)
        if 'slots' in data:
            data['slots'] = [TimeSlot.decode(slot) for slot in data['slots']]
        return Partition(**data)


class Workflow(ResourceBase):
    """Workflow class.

    Representation of a workflow, tasks and dependencies between
    those tasks.
    """

    def __init__(self, name, levels=[]):
        """Workflow constructor.

        Initialize a new workflow.
        """
        # TODO
        self.name = name
        self.levels = levels

    def insert(self, task, level=0):
        """Insert the task into the workflow.

        This method inserts a task at particular "level" of the
        workflow which is what handles the ordering of dependent tasks.
        So a task A that needs to run before a task B should be put in
        a level L and B should be put in a level L + 1.
        :param task: task to insert
        :type task: instance of Task
        :param level: level to insert at (starting at 0)
        :type level: int
        """
        while len(self.levels) <= level:
            self.levels.append([])
        self.levels[level].append(task)

    def encode(self):
        """Encode an object and return the basic type.

        Encodes the object and returns a basic type that can be
        converted to JSON or YAML.
        """
        val = dict(self.__dict__)
        for i, l in enumerate(val['levels']):
            val['levels'][i] = list(l)
            for j, t in enumerate(val['levels'][i]):
                val['levels'][i][j] = t.encode()
        return val

    @staticmethod
    def decode(data):
        """Decode a basic type and return the object it represents.

        Decodes basic Python types and returns a newly constructed
        object.
        """
        val = dict(data)
        levels = []
        for l in data['levels']:
            level = []
            for t in l:
                level.append(Task.decode(t))
            levels.append(level)
        val['levels'] = levels
        return Workflow(**val)


class Task(ResourceBase):
    """Task class.

    Representation of a single Task within a Workflow.
    """

    def __init__(self, name, runtime):
        """Task constructor.

        Initialize a new Task .
        :param name: name of the task
        :type name: str
        :param runtime: estimated runtime seconds
        :type runtime: int
        """
        self.name = name
        self.runtime = runtime

    def encode(self):
        """Encode an object and return the basic type.

        Encodes the object and returns a basic type that can be
        converted to JSON or YAML.
        """
        return dict(self.__dict__)

    @staticmethod
    def decode(data):
        """Decode a basic type and return the object it represents.

        Decodes basic Python types and returns a newly constructed
        object.
        """
        return Task(**data)


# TODO: Determine if a factory is the right way to go about this
class SchedulerFactory(ResourceBase):
    """SchedulerFactory class.

    Class used for creating new schedulers based on known circumstances.
    """

    # TODO
    def __init__(self):
        """SchedulerFactory constructor.

        Initialize a new SchedulerFactory .
        """
        # TODO

    def create(self):
        """Create a new scheduler.

        Creates a new scheduler and returns it.
        """
        # TODO

    def encode(self):
        """Encode an object and return the basic type.

        Encodes the object and returns a basic type that can be
        converted to JSON or YAML.
        """
        # TODO

    @staticmethod
    def decode(data):
        """Decode a basic type and return the object it represents.

        Decodes basic Python types and returns a newly constructed
        object.
        """
        # TODO


def schedule_next_fcfs(task, clusters, min_start_time):
    """Schedule the next task using fcfs.

    Schedule this task using fcfs at the minimum start time possible
    on open partitions within the list of allocations.
    :param task: a task
    :type task: dict of task name and runtime
    :param clusters: available clusters
    :type clusters: list of Cluster instances
    :param min_start_time: earliest time to schedule the task
    :type min_start_time: int
    """
    # TODO: Make it easier to iterate over different types of resources
    best_time = math.inf
    best_partition = None
    for cluster in clusters:
        for partition in cluster.partitions:
            t = partition.fit(task, start_time=min_start_time)
            if t < best_time:
                best_time = t
                best_partition = partition
    # Insert the time
    return best_partition.insert(task, start_time=best_time)

def fcfs(workflow, clusters, start_time):
    """Run the FCFS scheduling algorithm.

    Starts the FCFS algorithm with the given workflow and available clusters.
    :param workflow: the workflow
    :type workflow: instance of Workflow
    :param clusters: a list of available clusters
    :type clusters: list of instances of Cluster
    :param start_time: desired start time of the workflow
    :type start_time: int
    :rtype: dict from task name to instance of TimeSlot
    """
    provision = {}
    time = start_time
    # TODO: Something may be off with the time here
    for level in workflow.levels:
        max_time = time
        for task in level:
            slot = schedule_next_fcfs(task, clusters, time)
            provision[task.name] = slot
            # Update the time to the latest estimated completion time of
            # the level
            t = slot.start_time + task.runtime
            if t > max_time:
                max_time = t
        time = max_time
    return provision
