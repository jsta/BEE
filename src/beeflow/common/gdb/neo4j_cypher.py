"""Neo4j/Cypher transaction functions used by the Neo4jDriver class."""


def constrain_tasks_unique(tx):
    """Constrain tasks to have unique names."""
    unique_task_query = ("CREATE CONSTRAINT ON (t:Task) "
                         "ASSERT t.id IS UNIQUE")

    tx.run(unique_task_query)


def create_workflow_node(tx, workflow):
    """Create a Workflow node in the Neo4j database.

    The workflow node is the entry point to the workflow.
    :param workflow: the workflow description
    :type workflow: Workflow
    """
    workflow_query = ("CREATE (w:Workflow) "
                      "SET w.id = $workflow_id "
                      "SET w.name = $name")

    # Store the workflow ID and name in a new workflow node
    tx.run(workflow_query, workflow_id=workflow.id, name=workflow.name)


def create_workflow_hint_nodes(tx, hints):
    """Create Hint nodes for the workflow.

    :param hints: the workflow hints
    :type hints: list of Hint
    """
    for hint in hints:
        hint_query = ("MATCH (w:Workflow) "
                      "CREATE (w)-[:HAS_HINT]->(h:Hint $params) "
                      "SET h.class = $class_")

        tx.run(hint_query, params=hint.params, class_=hint.class_)


def create_workflow_requirement_nodes(tx, requirements):
    """Create Requirement nodes for the workflow.

    :param requirements: the workflow requirements
    :type requirements: list of Requirement
    """
    for req in requirements:
        req_query = ("MATCH (w:Workflow) "
                     "CREATE (w)-[:HAS_REQUIREMENT]->(r:Requirement $params) "
                     "SET r.class = $class_")

        tx.run(req_query, params=req.params, class_=req.class_)


def create_workflow_input_nodes(tx, inputs):
    """Create Input nodes for the workflow.

    :param inputs: the workflow inputs
    :type inputs: list of InputParameter"""
    for input_ in inputs:
        input_query = ("MATCH (w:Workflow) CREATE (w)-[:HAS_INPUT]->(i:Input) "
                       "SET i.id = $input_id "
                       "SET i.type = $type "
                       "SET i.value = $value")

        tx.run(input_query, input_id=input_.id, type=input_.type, value=input_.value)


def create_workflow_output_nodes(tx, outputs):
    """Create Output nodes for the workflow.

    :param outputs: the workflow outputs
    :type outputs: list of OutputParameter"""
    for output in outputs:
        output_query = ("MATCH (w:Workflow) CREATE (w)-[:HAS_OUTPUT]->(o:Output) "
                        "SET o.id = $output_id "
                        "SET o.type = $type "
                        "SET o.value = $value "
                        "SET o.source = $source")

        tx.run(output_query, output_id=output.id, type=output.type, value=output.value,
               source=output.source)


def create_task(tx, task):
    """Create a Task node in the Neo4j database.

    :param task: the new task to create
    :type task: Task
    """
    create_query = ("CREATE (t:Task) "
                    "SET t.id = $task_id "
                    "SET t.workflow_id = $workflow_id "
                    "SET t.name = $name "
                    "SET t.base_command = $base_command "
                    "SET t.stdout = $stdout")

    # Unpack requirements, hints dictionaries into flat list
    tx.run(create_query, task_id=task.id, workflow_id=task.workflow_id, name=task.name,
           base_command=task.base_command, stdout=task.stdout)


def create_task_hint_nodes(tx, task):
    """Create Hint nodes for a task.

    :param task: the task whose hints to add to the graph
    :type task: Task
    """
    for hint in task.hints:
        hint_query = ("MATCH (t:Task {id: $task_id}) "
                      "CREATE (t)-[:HAS_HINT]->(h:Hint $params) "
                      "SET h.class = $class_")

        tx.run(hint_query, task_id=task.id, params=hint.params, class_=hint.class_)


def create_task_requirement_nodes(tx, task):
    """Create Requirement nodes for a task.

    :param task: the task whose requirements to add to the graph
    :type task: Task
    """
    for req in task.requirements:
        req_query = ("MATCH (t:Task {id: $task_id}) "
                     "CREATE (t)-[:HAS_REQUIREMENT]->(r:Requirement $params) "
                     "SET r.class = $class_")

        tx.run(req_query, task_id=task.id, params=req.params, class_=req.class_)


def create_task_input_nodes(tx, task):
    """Create Input nodes for a task.

    :param task: the task whose inputs to add to the graph
    :type task: Task"""
    for input_ in task.inputs:
        input_query = ("MATCH (t:Task {id: $task_id}) "
                       "CREATE (t)-[:HAS_INPUT]->(i:Input) "
                       "SET i.id = $input_id "
                       "SET i.type = $type "
                       "SET i.value = $value "
                       "SET i.default = $default "
                       "SET i.source = $source "
                       "SET i.prefix = $prefix "
                       "SET i.position = $position")

        tx.run(input_query, task_id=task.id, input_id=input_.id, type=input_.type,
               value=input_.value, default=input_.default, source=input_.source,
               prefix=input_.prefix, position=input_.position)


def create_task_output_nodes(tx, task):
    """Create Output nodes for a task.

    :param task: the task whose outputs to add to the graph
    :type task: Task"""
    for output in task.outputs:
        output_query = ("MATCH (t:Task {id: $task_id}) "
                        "CREATE (t)-[:HAS_OUTPUT]->(o:Output) "
                        "SET o.id = $output_id "
                        "SET o.type = $type "
                        "SET o.value = $value "
                        "SET o.glob = $glob")

        tx.run(output_query, task_id=task.id, output_id=output.id, type=output.type,
               value=output.value, glob=output.glob)


def create_task_metadata_node(tx, task):
    """Create a task metadata node in the Neo4j database.

    The node holds metadata about a task's execution state.

    :param task: the task for which to create a metadata node
    :type task: Task
    """
    metadata_query = ("MATCH (t:Task {id: $task_id}) "
                      "CREATE (m:Metadata {state: 'WAITING'})-[:DESCRIBES]->(t)")

    tx.run(metadata_query, task_id=task.id)


def add_dependencies(tx, task):
    """Create dependencies between tasks.

    :param task: the workflow task
    :type task: Task
    """
    begins_query = ("MATCH (s:Task {id: $task_id})-[:HAS_INPUT]->(i:Input) "
                    "WITH s, collect(i.source) AS sources "
                    "MATCH (w:Workflow)-[:HAS_INPUT]->(i:Input) "
                    "WITH s, w, sources, collect(i.id) AS inputs "
                    "WHERE any(input IN sources WHERE input IN inputs) "
                    "MERGE (s)-[:BEGINS]->(w)")
    dependency_query = ("MATCH (s:Task {id: $task_id})-[:HAS_INPUT]->(i:Input) "
                        "WITH s, collect(i.source) as sources "
                        "MATCH (t:Task)-[:HAS_OUTPUT]->(o:Output) "
                        "WITH s, t, sources, collect(o.id) as outputs "
                        "WHERE any(input IN sources WHERE input IN outputs) "
                        "MERGE (s)-[:DEPENDS]->(t) "
                        "WITH s "
                        "MATCH (s)-[:HAS_OUTPUT]->(o:Output) "
                        "WITH s, collect(o.id) AS outputs "
                        "MATCH (t:Task)-[:HAS_INPUT]->(i:Input) "
                        "WITH s, t, outputs, collect(i.source) as sources "
                        "WHERE any(output IN outputs WHERE output IN sources) "
                        "MERGE (t)-[:DEPENDS]->(s)")

    tx.run(begins_query, task_id=task.id)
    tx.run(dependency_query, task_id=task.id)


def get_task_by_id(tx, task_id):
    """Get a workflow task from the Neo4j database by its ID.

    :param task_id: the task's ID
    :type task_id: str
    :rtype: BoltStatementResult
    """
    task_query = "MATCH (t:Task {id: $task_id}) RETURN t"

    return tx.run(task_query, task_id=task_id).single()


def get_task_hints(tx, task_id):
    """Get task hints from the Neo4j database by the task's ID.

    :param task_id: the task's ID
    :type task_id: str
    :rtype: BoltStatementResult
    """
    hints_query = "MATCH (:Task {id: $task_id})-[:HAS_HINT]->(h:Hint) RETURN h"

    return tx.run(hints_query, task_id=task_id)


def get_task_requirements(tx, task_id):
    """Get task requirements from the Neo4j database by the task's ID.

    :param task_id: the task's ID
    :type task_id: str
    :rtype: BoltStatementResult
    """
    reqs_query = "MATCH (:Task {id: $task_id})-[:HAS_REQUIREMENT]->(r:Requirement) RETURN r"

    return tx.run(reqs_query, task_id=task_id)


def get_task_inputs(tx, task_id):
    """Get task inputs from the Neo4j database by the task's ID.

    :param task_id: the task's ID
    :type task_id: str
    :rtype: BoltStatementResult
    """
    inputs_query = "MATCH (:Task {id: $task_id})-[:HAS_INPUT]->(i:Input) RETURN i"

    return tx.run(inputs_query, task_id=task_id)


def get_task_outputs(tx, task_id):
    """Get task outputs from the Neo4j database by the task's ID.

    :param task_id: the task's ID
    :type task_id: str
    :rtype: BoltStatementResult
    """
    outputs_query = "MATCH (:Task {id: $task_id})-[:HAS_OUTPUT]->(o:Output) RETURN o"

    return tx.run(outputs_query, task_id=task_id)


def get_workflow_description(tx):
    """Get the workflow description from the Neo4j database.

    :rtype: BoltStatementResult
    """
    workflow_desc_query = "MATCH (w:Workflow) RETURN w"

    return tx.run(workflow_desc_query).single()


def get_workflow_tasks(tx):
    """Get workflow tasks from the Neo4j database.

    :rtype: BoltStatementResult
    """
    workflow_query = "MATCH (t:Task) RETURN t"

    return tx.run(workflow_query)


def get_workflow_requirements(tx):
    """Get workflow requirements from the Neo4j database.

    :rtype: BoltStatementResult
    """
    requirements_query = "MATCH (:Workflow)-[:HAS_REQUIREMENT]->(r:Requirement) RETURN r"

    return tx.run(requirements_query)


def get_workflow_hints(tx):
    """Get workflow hints from the Neo4j database.

    :rtype: BoltStatementResult
    """
    hints_query = "MATCH (:Workflow)-[:HAS_HINT]->(h:Hint) RETURN h"

    return tx.run(hints_query)


def get_workflow_inputs(tx):
    """Get workflow inputs from the Neo4j database.

    :rtype: BoltStatementResult
    """
    inputs_query = "MATCH (:Workflow)-[:HAS_INPUT]->(i:Input) RETURN i"

    return tx.run(inputs_query)


def get_workflow_outputs(tx):
    """Get workflow outputs from the Neo4j database.

    :rtype BoltStatementResult
    """
    outputs_query = "MATCH (:Workflow)-[:HAS_OUTPUT]->(o:Output) RETURN o"

    return tx.run(outputs_query)


def get_ready_tasks(tx):
    """Get all tasks that are ready to execute.

    :rtype: BoltStatementResult
    """
    get_ready_query = "MATCH (:Metadata {state: 'READY'})-[:DESCRIBES]->(t:Task) RETURN t"

    return tx.run(get_ready_query)


def get_dependent_tasks(tx, task):
    """Get the tasks that depend on a specified task.

    :param task: the task whose dependencies to obtain
    :type task: Task
    :rtype: BoltStatementResult
    """
    dependents_query = "MATCH (t:Task)-[:DEPENDS]->(:Task {id: $task_id}) RETURN t"

    return tx.run(dependents_query, task_id=task.id)


def get_task_state(tx, task):
    """Get the state of a task.

    :param task: the task whose state to get
    :type task: Task
    :rtype: str
    """
    state_query = "MATCH (m:Metadata)-[:DESCRIBES]->(:Task {id: $task_id}) RETURN m.state"

    return tx.run(state_query, task_id=task.id).single().value()


def set_task_state(tx, task, state):
    """Set a task's state.

    :param task: the task whose state to set
    :type task: Task
    :param state: the new task state
    :type state: str
    """
    state_query = ("MATCH (m:Metadata)-[:DESCRIBES]->(:Task {id: $task_id}) "
                   "SET m.state = $state")

    tx.run(state_query, task_id=task.id, state=state)


def get_task_metadata(tx, task):
    """Get a task's metadata.

    :param task: the task whose metadata to get
    :type task: Task
    :rtype: BoltStatementResult
    """
    metadata_query = "MATCH (m:Metadata)-[:DESCRIBES]->(:Task {id: $task_id}) RETURN m"

    return tx.run(metadata_query, task_id=task.id).single()


def set_task_metadata(tx, task, metadata):
    """Set a task's metadata.

    :param task: the task whose metadata to set
    :type task: Task
    :param metadata: the task metadata
    :type metadata: dict
    """
    metadata_query = "MATCH (m:Metadata)-[:DESCRIBES]->(:Task {id: $task_id})"

    # TODO: remove injection vulnerability before release
    for k, v in metadata.items():
        if isinstance(v, str):
            metadata_query += f" SET m.{k} = '{v}'"
        else:
            metadata_query += f" SET m.{k} = {v}"

    tx.run(metadata_query, task_id=task.id)


def set_task_output(tx, task, output_id, value):
    """Set a task's output value.

    :param task: the task whose output to set
    :type task: Task
    :param output_id: the ID of the output to set
    :type output_id: str
    :param value: the value of the output
    :type value: str
    """
    output_query = ("MATCH (:Task {id: $task_id})-[:HAS_OUTPUT]->(o:Output {id: $output_id}) "
                    "SET o.value = $value")

    tx.run(output_query, task_id=task.id, output_id=output_id, value=value)


def set_init_tasks_to_ready(tx):
    """Set the initial workflow tasks' states to 'READY'."""
    init_ready_query = ("MATCH (m:Metadata)-[:DESCRIBES]->(t:Task)-[:BEGINS]->(:Workflow) "
                        "WHERE NOT (t)-[:DEPENDS]->(:Task) "
                        "SET m.state = 'READY'")

    tx.run(init_ready_query)


def set_init_task_inputs(tx):
    """Set the initial workflow tasks' inputs from workfow inputs or defaults if necessary."""
    task_inputs_query = ("MATCH (i:Input)<-[:HAS_INPUT]-(:Task)-[:BEGINS]->(:Workflow)"
                         "-[:HAS_INPUT]->(wi:Input) "
                         "WHERE i.source = wi.id AND wi.value IS NOT NULL "
                         "SET i.value = wi.value")
    # Set any values to defaults if necessary
    defaults_query = ("MATCH (i:Input)<-[:HAS_INPUT]-(t:Task)-[:BEGINS]->(:Workflow)"
                      "-[:HAS_INPUT]->(wi:Input) "
                      "WHERE i.source = wi.id "
                      "AND i.value IS NULL AND i.default IS NOT NULL "
                      "SET i.value = i.default")

    tx.run(task_inputs_query)
    tx.run(defaults_query)


def copy_task_outputs(tx, task):
    """Use task outputs to set dependent task inputs or workflow outputs.

    Sets dependent task inputs to default value if necessary.

    :param task: the task whose outputs to set
    :type task: Task
    """
    task_inputs_query = ("MATCH (i:Input)<-[:HAS_INPUT]-(:Task)-[:DEPENDS]->"
                         "(t:Task {id: $task_id})-[:HAS_OUTPUT]->(o:Output) "
                         "WHERE i.source = o.id AND o.value IS NOT NULL "
                         "SET i.value = o.value")
    # Set any values to defaults if necessary
    defaults_query = ("MATCH (m:Metadata)-[:DESCRIBES]->(:Task)<-[:DEPENDS]-"
                      "(t:Task)-[:DEPENDS]->(:Task {id: $task_id}) "
                      "WITH m, t "
                      "MATCH (t)-[:HAS_INPUT]->(i:Input) "
                      "WITH i, collect(m) AS mlist "
                      "WHERE all(m IN mlist WHERE m.state = 'COMPLETED') "
                      "AND i.value IS NULL AND i.default IS NOT NULL "
                      "SET i.value = i.default")
    workflow_output_query = ("MATCH (:Workflow)-[:HAS_OUTPUT]->(wo:Output) "
                             "WITH wo "
                             "MATCH (t:Task {id: $task_id})-[:HAS_OUTPUT]->(o:Output) "
                             "WHERE wo.source = o.id "
                             "SET wo.value = o.value")

    tx.run(task_inputs_query, task_id=task.id)
    tx.run(defaults_query, task_id=task.id)
    tx.run(workflow_output_query, task_id=task.id)


def set_running_tasks_to_paused(tx):
    """Set 'RUNNING' task states to 'PAUSED'."""
    set_paused_query = ("MATCH (m:Metadata {state: 'RUNNING'})-[:DESCRIBES]->(:Task) "
                        "SET m.state = 'PAUSED'")

    tx.run(set_paused_query)


def set_paused_tasks_to_running(tx):
    """Set 'PAUSED' task states to 'RUNNING'."""
    set_running_query = ("MATCH (m:Metadata {state: 'PAUSED'})-[:DESCRIBES]->(:Task) "
                         "SET m.state = 'RUNNING'")

    tx.run(set_running_query)


def set_runnable_tasks_to_ready(tx):
    """Set task states to 'READY' if all required inputs have values."""
    set_runnable_ready_query = ("MATCH (m:Metadata)-[:DESCRIBES]->"
                                "(t:Task)-[:HAS_INPUT]->(i:Input) "
                                "WITH m, t, collect(i) AS ilist "
                                "WHERE m.state = 'WAITING' "
                                "AND all(i IN ilist WHERE i.value IS NOT NULL) "
                                "SET m.state = 'READY'")

    tx.run(set_runnable_ready_query)


def reset_tasks_metadata(tx):
    """Reset the metadata for each of a workflow's tasks."""
    reset_metadata_query = ("MATCH (m:Metadata)-[:DESCRIBES]->(t:Task) "
                            "DETACH DELETE m "
                            "WITH t "
                            "CREATE (:Metadata {state: 'WAITING'})-[:DESCRIBES]->(t)")

    tx.run(reset_metadata_query)


def reset_workflow_id(tx, new_id):
    """Reset the workflow ID of the workflow using uuid4.

    :param new_id: the new workflow ID
    :type new_id: str
    """
    reset_workflow_id_query = ("MATCH (w:Workflow), (t:Task) "
                               "SET w.id = $new_id "
                               "SET t.workflow_id = $new_id")

    tx.run(reset_workflow_id_query, new_id=new_id)


def all_tasks_completed(tx):
    """Return true if all of a workflow's tasks have state 'COMPLETED'.

    :rtype: bool
    """
    not_completed_query = ("MATCH (m:Metadata)-[:DESCRIBES]->(t:Task) "
                           "WHERE m.state <> 'COMPLETED' "
                           "RETURN t IS NOT NULL LIMIT 1")

    # False if at least one task with state not 'COMPLETED'
    return bool(tx.run(not_completed_query).single() is None)


def is_empty(tx):
    """Return true if the database is empty, else false.

    :rtype: bool
    """
    empty_query = "MATCH (n) RETURN n IS NULL LIMIT 1"

    # False if at least one task
    return bool(tx.run(empty_query).single() is None)


def cleanup(tx):
    """Clean up all workflow data in the database."""
    cleanup_query = "MATCH (n) DETACH DELETE n"

    tx.run(cleanup_query)
