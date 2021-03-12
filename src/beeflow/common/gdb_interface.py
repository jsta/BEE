"""Mid-level interface for managing a graph database with workflows.

Delegates the actual work to an instance of a subclass of
the abstract base class GraphDatabaseDriver. By default,
this is the Neo4jDriver class.
"""

from beeflow.common.gdb.neo4j_driver import Neo4jDriver


class GraphDatabaseInterface:
    """Interface for managing a graph database with workflows.

    Requires an implemented subclass of GraphDatabaseDriver (uses Neo4jDriver by default).
    """

    def __init__(self, gdb_driver=Neo4jDriver):
        """Initialize the graph database interface with a graph database driver.

        :param gdb_driver: the graph database driver (Neo4jDriver by default)
        :type gdb_driver: subclass of GraphDatabaseDriver
        """
        # Store the GDB driver state
        self._gdb_driver = gdb_driver
        self._connection = None

    def __del__(self):
        """Disconnect from the graph database when interface deconstructs."""
        if self.initialized():
            self.close()

    def connect(self, **kwargs):
        """Initialize a graph database interface with a driver.

        :param kwargs: arguments for initializing the graph database connection
        """
        print('gdbi passing kwargs')
        # Initialize the graph database driver
        self._connection = self._gdb_driver(**kwargs)

    def initialize_workflow(self, workflow):
        """Begin construction of a workflow in the graph database.

        Connects to the database and creates the Workflow with accompanying Hint
        and Requirement nodes.
        Permits the addition of task nodes to the workflow.

        :param workflow: the workflow description
        :type workflow: Workflow
        """
        self._connection.initialize_workflow(workflow)

    def execute_workflow(self):
        """Begin execution of the loaded workflow."""
        self._connection.execute_workflow()

    def load_task(self, task):
        """Load a task into the workflow in the graph database.

        :param task: the workflow task
        :type task: Task
        """
        self._connection.load_task(task)

    def get_task_by_id(self, task_id):
        """Return a workflow Task given its ID.

        :param task_id: the task's ID
        :type task_id: str
        :rtype: Task
        """
        return self._connection.get_task_by_id(task_id)

    def get_workflow_description(self):
        """Return the workflow description from the graph database.

        :rtype: Workflow
        """
        return self._connection.get_workflow_description()

    def get_workflow_tasks(self):
        """Return a workflow's tasks from the graph database.

        :rtype: set of Task
        """
        return self._connection.get_workflow_tasks()

    def get_workflow_requirements_and_hints(self):
        """Return a tuple containing a list of requirements and a list of hints.

        The returned tuple format is (requirements, hints).

        :rtype: (set of Requirement, set of Hint)
        """
        return self._connection.get_workflow_requirements_and_hints()

    def get_subworkflow_tasks(self, subworkflow):
        """Return a subworkflow's Task objects from the graph database.

        :param subworkflow: the unique identifier of the subworkflow
        :type subworkflow: str
        :rtype: set of Task
        """
        return self._connection.get_subworkflow_tasks(subworkflow)

    def get_dependent_tasks(self, task):
        """Return the dependents of a task in a graph database workflow.

        :param task: the task whose dependents to retrieve
        :type task: Task
        :rtype: set of Task
        """
        return self._connection.get_dependent_tasks(task)

    def get_task_state(self, task):
        """Return the state of a task in a graph database workflow.

        :param task: the task whose state to retrieve
        :type task: Task
        :rtype: str
        """
        return self._connection.get_task_state(task)

    def set_task_state(self, task, state):
        """Set the state of a task in the graph database workflow.

        :param task: the task whose state to change
        :type task: Task
        :param state: the new state
        :type state: str
        """
        return self._connection.set_task_state(task, state)

    def initialized(self):
        """Return true if the database connection has been initialized, else false.

        :rtype: bool
        """
        return bool(self._connection is not None)

    def empty(self):
        """Return true if the graph database is empty, else false.

        :rtype: bool
        """
        return self._connection.empty()

    def cleanup(self):
        """Clean up all data in the graph database."""
        self._connection.cleanup()

    def close(self):
        """Close the connection to the graph database."""
        self._connection.close()
