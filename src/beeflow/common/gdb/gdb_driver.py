"""Abstract base class for the handling of workflow DAGs."""

from abc import ABC, abstractmethod


class GraphDatabaseDriver(ABC):
    """Driver interface for a generic graph database.

    The driver must implement a __init__ method that creates/connects to
    the graph database and returns some kind of 'connection' interface object.
    """

    @abstractmethod
    def initialize_workflow(self, workflow):
        """Begin construction of a workflow in the graph database.

        Create the Workflow, Requirement, and Hint nodes in the graph database.

        :param workflow: the workflow description
        :type workflow: Workflow
        """

    @abstractmethod
    def execute_workflow(self):
        """Begin execution of the stored workflow.

        Set the initial tasks' states to ready.
        """

    @abstractmethod
    def load_task(self, task):
        """Load a task into the stored workflow.

        Dependencies should be automatically deduced and generated by the graph database
        upon loading each task by matching task inputs and outputs.

        :param task: a workflow task
        :type task: Task
        """

    @abstractmethod
    def get_task_by_id(self, task_id):
        """Return a workflow task record from the graph database.

        :param task_id: a task's ID
        :type task_id: str
        :rtype: Task
        """

    @abstractmethod
    def get_workflow_description(self):
        """Return a reconstructed Workflow object from the graph database.

        :rtype: Workflow
        """
    @abstractmethod
    def get_workflow_tasks(self):
        """Return a list of all workflow task records from the graph database.

        :rtype: set of Task
        """

    @abstractmethod
    def get_workflow_requirements_and_hints(self):
        """Return all workflow requirements and hints from the graph database.

        Must return a tuple with the format (requirements, hints)

        :rtype: (set of Requirement, set of Hint)
        """

    @abstractmethod
    def get_subworkflow_tasks(self, subworkflow):
        """Return a list of subworkflow task records from the graph database.

        :param subworkflow: the unique identifier of the subworkflow
        :type subworkflow: str
        :rtype: set of Task
        """

    @abstractmethod
    def get_dependent_tasks(self, task):
        """Return the dependent tasks of a workflow task in the graph database.

        :param task: the task whose dependents to retrieve
        :type task: Task
        :rtype: set of Task
        """

    @abstractmethod
    def get_task_state(self, task):
        """Return the state of a task in the graph database workflow.

        :param task: the task whose status to retrieve
        :type task: Task
        :rtype: str
        """

    @abstractmethod
    def set_task_state(self, task, state):
        """Set the state of a task in the graph database workflow.

        :param task: the task whose state to change
        :type task: Task
        :param state: the new state
        :type state: str
        """

    @abstractmethod
    def empty(self):
        """Determine if the database is empty.

        :rtype: bool
        """

    @abstractmethod
    def cleanup(self):
        """Clean up all the data stored in the graph database."""

    @abstractmethod
    def close(self):
        """Close the connection to the graph database."""
