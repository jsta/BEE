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

        Should create the Workflow, Requirement, and Hint nodes in the graph database.

        :param workflow: the workflow description
        :type workflow: Workflow
        """

    @abstractmethod
    def execute_workflow(self):
        """Begin execution of the stored workflow.

        Set the initial tasks' states to 'READY'.
        """

    @abstractmethod
    def pause_workflow(self):
        """Pause execution of a running workflow.

        Set workflow from state 'RUNNING' to 'PAUSED'.
        """

    @abstractmethod
    def resume_workflow(self):
        """Resume execution of a paused workflow.

        Set workflow state from 'PAUSED' to 'RUNNING'.
        """

    @abstractmethod
    def reset_workflow(self, new_id):
        """Reset the execution state of a stored workflow.

        Set all task states to 'WAITING'.
        Change the workflow ID of the Workflow and Task nodes to new_id.
        Delete all task metadata except for task state.

        :param new_id: the new workflow ID
        :type new_id: str
        """

    @abstractmethod
    def load_task(self, task):
        """Load a task into a stored workflow.

        Dependencies should be automatically deduced and generated by the graph database
        upon loading each task by matching workflow inputs with new task inputs,
        or task outputs with new task inputs.

        :param task: a workflow task
        :type task: Task
        """

    @abstractmethod
    def initialize_ready_tasks(self):
        """Set runnable tasks to state 'READY'.

        Runnable tasks are tasks with all input dependencies fulfilled.
        """
    
    @abstractmethod
    def restart_task(self, old_task, new_task):
        """Restart a failed task.
        
        Create a Task node for new_task with state 'RESTARTED' and an edge
        to indicate that it is the child of the Task node of old_task.

        :param old_task: the failed task
        :type old_task: Task
        :param new_task: the new (restarted) task
        :type new_task: Task
        """

    @abstractmethod
    def finalize_task(self, task):
        """Set task state to 'COMPLETED' and set inputs from source.
        
        :param task: the task to finalize
        :type task: Task
        """

    @abstractmethod
    def get_task_by_id(self, task_id):
        """Return a reconstructed Task object from the graph database by its ID.

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
    def get_workflow_state(self):
        """Return the current state of the workflow

        :rtype: str
        """

    @abstractmethod
    def get_workflow_tasks(self):
        """Return a list of all workflow tasks from the graph database.

        :rtype: list of Task
        """

    @abstractmethod
    def get_workflow_requirements_and_hints(self):
        """Return all workflow requirements and hints from the graph database.

        Must return a tuple with the format (requirements, hints)

        :rtype: (list of Requirement, list of Hint)
        """

    @abstractmethod
    def get_workflow_inputs_and_outputs(self):
        """Return all workflow inputs and outputs from the graph database.

        Returns a tuple of (inputs, outputs).

        :rtype: (list of InputParameter, list of OutputParameter)
        """

    @abstractmethod
    def get_ready_tasks(self):
        """Return tasks with state 'READY' from the graph database.

        :rtype: list of Task
        """

    @abstractmethod
    def get_dependent_tasks(self, task):
        """Return the dependent tasks of a workflow task in the graph database.

        :param task: the task whose dependents to retrieve
        :type task: Task
        :rtype: list of Task
        """

    @abstractmethod
    def get_task_state(self, task):
        """Return the state of a task in the graph database.

        :param task: the task whose status to retrieve
        :type task: Task
        :rtype: str
        """

    @abstractmethod
    def set_task_state(self, task, state):
        """Set the state of a task in the graph database.

        :param task: the task whose state to set
        :type task: Task
        :param state: the new state
        :type state: str
        """

    @abstractmethod
    def get_task_metadata(self, task):
        """Return the metadata of a task in the graph database.

        :param task: the task whose metadata to retrieve
        :type task: Task
        :rtype: dict
        """

    @abstractmethod
    def set_task_metadata(self, task, metadata):
        """Set the metadata of a task in the graph database.

        :param task: the task whose metadata to set
        :type task: Task
        :param metadata: the job description metadata
        :type metadata: dict
        """

    @abstractmethod
    def get_task_input(self, task, input_id):
        """Get a task input object.

        :param task: the task whose input to retrieve
        :type task: Task
        :param input_id: the ID of the input
        :type input_id: str
        :rtype: StepInput
        """

    @abstractmethod
    def set_task_input(self, task, input_id, value):
        """Set the value of a task input.

        :param task: the task whose input to set
        :type task: Task
        :param input_id: the ID of the input
        :type input_id: str
        :param value: str or int or float
        """

    @abstractmethod
    def get_task_output(self, task, output_id):
        """Get a task output object.

        :param task: the task whose output to retrieve
        :type task: Task
        :param output_id: the ID of the output
        :type output_id: str
        :rtype: StepOutput
        """

    @abstractmethod
    def set_task_output(self, task, output_id, value):
        """Set the value of a task output.

        :param task: the task whose output to set
        :type task: Task
        :param output_id: the ID of the output
        :type output_id: str
        :param value: the output value to set
        :type value: str or int or float
        """

    @abstractmethod
    def set_task_input_type(self, task, input_id, type_):
        """Set the type of a task input.

        :param task: the task whose input type to set
        :type task: Task
        :param input_id: the ID of the input
        :type input_id: str
        :param type_: the input type to set
        :param type_: str
        """

    @abstractmethod
    def set_task_output_glob(self, task, output_id, glob):
        """Set the glob of a task output.

        :param task: the task whose output glob to set
        :type task: Task
        :param output_id: the ID of the output
        :type output_id: str
        :param glob: the output glob to set
        :type glob: str
        """

    @abstractmethod
    def workflow_completed(self):
        """Determine if a workflow has completed.

        A workflow has completed if each of its final tasks has state 'COMPLETED'.

        :rtype: bool
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
