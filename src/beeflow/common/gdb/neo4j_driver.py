"""Neo4j interface module.

Connection requires a valid URI, Username, and Password.
The current defaults are defined below, but should later be
either standardized or read from a config file.
"""

from neo4j import GraphDatabase as Neo4jDatabase
from neobolt.exceptions import ServiceUnavailable

from beeflow.common.gdb.gdb_driver import GraphDatabaseDriver
from beeflow.common.gdb import neo4j_cypher as tx
from beeflow.common.wf_data import Workflow, Task, Requirement, Hint

# Default Neo4j authentication
# We may want to instead get these from a config at some point
DEFAULT_HOSTNAME = "localhost"
DEFAULT_BOLT_PORT = "7687"
DEFAULT_USER = "neo4j"
DEFAULT_PASSWORD = "password"


class Neo4jDriver(GraphDatabaseDriver):
    """The driver for a Neo4j Database.

    Implements GraphDatabaseDriver.
    Wraps the neo4j package proprietary driver.
    """

    def __init__(self, user=DEFAULT_USER, password=DEFAULT_PASSWORD, **kwargs):
        """Create a new Neo4j database driver.

        :param uri: the URI of the Neo4j database
        :type uri: str
        :param user: the username for the database user account
        :type user: str
        :param password: the password for the database user account
        :type password: str
        """
        db_hostname = kwargs.get("db_hostname", DEFAULT_HOSTNAME)
        bolt_port = kwargs.get("bolt_port", DEFAULT_BOLT_PORT)
        password = kwargs.get("db_pass", DEFAULT_PASSWORD)
        uri = f"bolt://{db_hostname}:{bolt_port}"

        try:
            # Connect to the Neo4j database using the Neo4j proprietary driver
            self._driver = Neo4jDatabase.driver(uri, auth=(user, password))
            # Require tasks to have unique names
            self._require_tasks_unique()
        except ServiceUnavailable:
            print("Neo4j database unavailable. Is it running?")

    def initialize_workflow(self, workflow):
        """Begin construction of a workflow stored in Neo4j.

        Creates the Workflow, Requirement, and Hint nodes in the Neo4j database.

        :param workflow: the workflow description
        :type workflow: Workflow
        """
        with self._driver.session() as session:
            session.write_transaction(tx.create_workflow_node, workflow)
            session.write_transaction(tx.create_workflow_requirement_nodes,
                                      requirements=workflow.requirements)
            session.write_transaction(tx.create_workflow_hint_nodes, hints=workflow.hints)

    def execute_workflow(self):
        """Begin execution of the workflow stored in the Neo4j database."""
        self._write_transaction(tx.set_init_tasks_to_ready)

    def pause_workflow(self):
        """Pause execution of a running workflow in Neo4j.

        Sets tasks with state 'RUNNING' to 'PAUSED'.
        """
        self._write_transaction(tx.set_running_tasks_to_paused)

    def resume_workflow(self):
        """Resume execution of a paused workflow in Neo4j.

        Sets tasks with state 'PAUSED' to 'RUNNING'.
        """
        self._write_transaction(tx.set_paused_tasks_to_running)

    def reset_workflow(self, new_id):
        """Reset the execution state of an entire workflow.

        Sets all task states to 'WAITING'.
        Changes the workflow ID of the Workflow and Task nodes with new_id.

        :param new_id: the new workflow ID
        :type new_id: str
        """
        with self._driver.session() as session:
            session.write_transaction(tx.reset_tasks_metadata)
            session.write_transaction(tx.reset_workflow_id, new_id=new_id)

    def load_task(self, task):
        """Load a task into a workflow stored in the Neo4j database.

        Dependencies are automatically deduced and generated by Neo4j upon loading
        each task by matching task inputs and outputs.

        Task hint nodes and metadata nodes are created for querying convenience.

        :param task: a workflow task
        :type task: Task
        """
        with self._driver.session() as session:
            session.write_transaction(tx.create_task, task=task)
            session.write_transaction(tx.create_task_hint_nodes, task=task)
            session.write_transaction(tx.create_task_requirement_nodes, task=task)
            session.write_transaction(tx.create_task_metadata_node, task=task)
            session.write_transaction(tx.add_dependencies, task=task)

    def initialize_ready_tasks(self):
        """Set runnable tasks to state 'READY'.

        Runnable tasks are tasks with all dependency tasks'
        states set to 'COMPLETED'.
        """
        self._write_transaction(tx.set_runnable_tasks_to_ready)

    def get_task_by_id(self, task_id):
        """Return a reconstructed task from the Neo4j database.

        :param task_id: a task's ID
        :type task_id: str
        :rtype: Task
        """
        task_record = self._read_transaction(tx.get_task_by_id, task_id=task_id)
        tuples = self._get_task_hint_req_tuples([task_record])
        return _reconstruct_task(tuples[0][0], tuples[0][1], tuples[0][2])

    def get_workflow_description(self):
        """Return a reconstructed Workflow object from the Neo4j database.

        :rtype: Workflow
        """
        requirements, hints = self.get_workflow_requirements_and_hints()
        workflow_record = self._read_transaction(tx.get_workflow_description)
        return _reconstruct_workflow(workflow_record, hints, requirements)

    def get_workflow_tasks(self):
        """Return all workflow task records from the Neo4j database.

        :rtype: set of Task
        """
        task_records = self._read_transaction(tx.get_workflow_tasks)
        tuples = self._get_task_hint_req_tuples(task_records)
        return {_reconstruct_task(tup[0], tup[1], tup[2]) for tup in tuples}

    def get_workflow_requirements_and_hints(self):
        """Return all workflow requirements and hints from the Neo4j database.

        Returns a tuple of (requirements, hints)

        :rtype: (set of Requirement, set of Hint)
        """
        with self._driver.session() as session:
            requirements = _reconstruct_requirements(
                session.read_transaction(tx.get_workflow_requirements))
            hints = _reconstruct_hints(session.read_transaction(tx.get_workflow_hints))
        return requirements, hints

    def get_subworkflow_tasks(self, subworkflow):
        """Return subworkflow tasks from the Neo4j database.

        :param subworkflow: the unique identifier of the subworkflow
        :type subworkflow: str
        :rtype: set of Task
        """
        task_records = self._read_transaction(tx.get_subworkflow_tasks, subworkflow=subworkflow)
        tuples = self._get_task_hint_req_tuples(task_records)
        return {_reconstruct_task(tup[0], tup[1], tup[2]) for tup in tuples}

    def get_ready_tasks(self):
        """Return tasks with state 'READY' from the graph database.

        :rtype: set of Task
        """
        task_records = self._read_transaction(tx.get_ready_tasks)
        tuples = self._get_task_hint_req_tuples(task_records)
        return {_reconstruct_task(tup[0], tup[1], tup[2]) for tup in tuples}

    def get_dependent_tasks(self, task):
        """Return the dependent tasks of a specified workflow task.

        :param task: the task whose dependents to retrieve
        :type task: Task
        :rtype: set of Task
        """
        task_records = self._read_transaction(tx.get_dependent_tasks, task=task)
        tuples = self._get_task_hint_req_tuples(task_records)
        return {_reconstruct_task(tup[0], tup[1], tup[2]) for tup in tuples}

    def get_task_state(self, task):
        """Return the state of a task in the Neo4j workflow.

        :param task: the task whose state to retrieve
        :type task: Task
        :rtype: str
        """
        return self._read_transaction(tx.get_task_state, task=task)

    def set_task_state(self, task, state):
        """Set the state of a task in the Neo4j workflow.

        :param task: the task whose state to change
        :type task: Task
        :param state: the new state
        :type state: str
        """
        self._write_transaction(tx.set_task_state, task=task, state=state)

    def get_task_metadata(self, task, keys):
        """Return the metadata of a task in the Neo4j workflow.

        :param task: the task whose metadata to retrieve
        :type task: Task
        :param keys: the metadata keys whose values to retrieve
        :type keys: iterable of str
        :rtype: dict
        """
        metadata_record = self._read_transaction(tx.get_task_metadata, task=task)
        return _reconstruct_metadata(metadata_record, keys)

    def set_task_metadata(self, task, metadata):
        """Set the metadata of a task in the Neo4j workflow.

        :param task: the task whose metadata to set
        :type task: Task
        :param metadata: the job description metadata
        :type metadata: dict
        """
        self._write_transaction(tx.set_task_metadata, task=task, metadata=metadata)

    def workflow_completed(self):
        """Determine if a workflow in the Neo4j database has completed.

        A workflow has completed if each of its tasks has state 'COMPLETED'.
        :rtype: bool
        """
        return self._read_transaction(tx.all_tasks_completed)

    def empty(self):
        """Determine if the Neo4j database is empty.

        :rtype: bool
        """
        return self._read_transaction(tx.is_empty)

    def cleanup(self):
        """Clean up all data in the Neo4j database."""
        self._write_transaction(tx.cleanup)

    def close(self):
        """Close the connection to the Neo4j database."""
        self._driver.close()

    def _get_task_hint_req_tuples(self, task_records):
        """Get a list of (task_record, hints, requirements) tuples.

        :param task_records: the database records of the tasks
        :type task_records: BoltStatementResult
        :rtype: list of (BoltStatementResult, set of Hint)
        """
        with self._driver.session() as session:
            trecords = list(task_records)
            hint_records = [session.read_transaction(tx.get_task_hints,
                            task_id=rec["t"]["task_id"]) for rec in trecords]
            req_records = [session.read_transaction(tx.get_task_requirements,
                           task_id=rec["t"]["task_id"]) for rec in trecords]
        hints = [_reconstruct_hints(hint_record) for hint_record in hint_records]
        reqs = [_reconstruct_requirements(req_record) for req_record in req_records]
        return list(zip(trecords, hints, reqs))

    def _require_tasks_unique(self):
        """Require tasks to have unique names."""
        self._write_transaction(tx.constrain_workflow_unique)

    def _read_transaction(self, tx_fun, **kwargs):
        """Run a Neo4j read transaction.

        :param tx_fun: the transaction function to run
        :type tx_fun: function
        :param kwargs: optional parameters for the transaction function
        """
        # Wrapper for neo4j.Session.read_transaction
        with self._driver.session() as session:
            result = session.read_transaction(tx_fun, **kwargs)
        return result

    def _write_transaction(self, tx_fun, **kwargs):
        """Run a Neo4j write transaction.

        :param tx_fun: the transaction function to run
        :type tx_fun: function
        :param kwargs: optional parameters for the transaction function
        """
        # Wrapper for neo4j.Session.write_transaction
        with self._driver.session() as session:
            session.write_transaction(tx_fun, **kwargs)


def _reconstruct_requirements(req_records):
    """Reconstruct requirements by their records retrieved from Neo4j.

    :param req_records: the database record of the requirements
    :type req_records: BoltStatementResult
    :rtype: set of Requirement
    """
    recs = [req_record["r"] for req_record in req_records]
    return {Requirement(rec["class"], rec["key"], rec["value"]) for rec in recs}


def _reconstruct_hints(hint_records):
    """Reconstruct hints by their records retrieved from Neo4j.

    :param hint_records: the database record of the hints
    :type hint_records: BoltStatementResult
    :rtype: set of Hint
    """
    recs = [hint_record["h"] for hint_record in hint_records]
    return {Hint(rec["class"], rec["key"], rec["value"]) for rec in recs}


def _reconstruct_workflow(workflow_record, hints, requirements):
    """Reconstruct a Workflow object by its record retrieved from Neo4j.

    :param workflow_record: the database record of the workflow
    :type workflow_record: BoltStatementResult
    :param hints: the workflow hints
    :type hints: set of Hint
    :param requirements: the workflow requirements
    :type requirements: set of Requirement
    :rtype: Workflow
    """
    rec = workflow_record["w"]
    return Workflow(hints=hints, requirements=requirements, inputs=set(rec["inputs"]),
                    outputs=set(rec["outputs"]), workflow_id=rec["workflow_id"])


def _reconstruct_task(task_record, hints, requirements):
    """Reconstruct a Task object by its record retrieved from Neo4j.

    :param task_record: the database record of the task
    :type task_record: BoltStatementResult
    :param hints: the task hints
    :type hints: set of Hint
    :rtype: Task
    """
    rec = task_record["t"]
    return Task(name=rec["name"], command=rec["command"], hints=hints, requirements=requirements,
                subworkflow=rec["subworkflow"], inputs=set(rec["inputs"]),
                outputs=set(rec["outputs"]), workflow_id=rec["workflow_id"],
                task_id=rec["task_id"])


def _reconstruct_metadata(metadata_record, keys):
    """Reconstruct a dict containing the job description metadata retrieved from Neo4j.

    :param metadata: the database record of the metadata
    :type metadata: dict
    :param keys: the metadata keys to retrieve from the record
    :type keys: iterable of str
    :rtype: dict
    """
    rec = metadata_record["m"]
    return {key: rec[key] for key in keys}
