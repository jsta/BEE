#!/usr/bin/env python3

# Argument parsing inspired by:
# "Writing sustainable Python scripts"
# https://vincent.bernat.ch/en/blog/2019-sustainable-python-script
#
# cwl-utils repo:
# https://github.com/common-workflow-language/cwl-utils
#
# Yes, this is ugly and undocumented. Will be cleaned up a documented
# when I move it into the main project structure.

"""Dump contents a CWL file.

This script will dump (display to terminal) the contents of a CWL file. The CWL
file is parsed using parser_v1_0.py from the cwl-utils repository. That parser
creates Python objects from the CWL file (as opposed to other parsing
techniques that produce Python dictionaries.

"""

import sys
import argparse
import uuid
import cwl_utils.parser_v1_0 as cwl
from beeflow.common.wf_interface import WorkflowInterface


class CWLCommandLineTool:
    """Creates a shell command from CWL."""

    def __init__(self, cwl_obj):
        """Initialize the shell command.

        param cwl_obj: must be a CWL CommandLineTool object
        """
        # processes CWL CommandInputParameter
        def _add_input(obj):
            arg = {}
            arg['id'] = obj.id
            arg['type'] = obj.type
            arg['position'] = obj.inputBinding.position
            self.inputs.append(arg)

        # processes CWL CommandOutputParameter
        def _add_output(obj):
            arg = {}
            arg['id'] = obj.id
            arg['type'] = obj.type
            self.outputs.append(arg)

        self.inputs = []
        self.outputs = []
        self.uuid = uuid.uuid4()
        self.base_command = cwl_obj.baseCommand
        for i in cwl_obj.inputs:
            _add_input(i)
        for i in cwl_obj.outputs:
            _add_output(i)

    def __str__(self):
        """Pretty print the shell command."""
        # multi-line using parens: https://stackoverflow.com/a/10660477/227441
        return(f"{self.uuid.hex}: CWLCommandLineTool\n"
               f"    {self.base_command} param param")



def cwl_dumper(obj):
    cwl_dumper_dict = {
        cwl.Workflow:                        create_workflow,
        cwl.InputParameter:                  get_wf_inputs,
        cwl.WorkflowOutputParameter:         get_wf_outputs,
        cwl.WorkflowStepInput:               dump_workflow_step_input,
        cwl.CommandLineTool:                 dump_command_line_tool,
        cwl.CommandInputParameter:           dump_command_input_parameter,
        cwl.CommandOutputParameter:          dump_command_output_parameter,
        cwl.CommandLineBinding:              dump_command_line_binding,
        cwl.ScatterFeatureRequirement:       dump_requirement,
        cwl.InlineJavascriptRequirement:     dump_requirement,
        cwl.StepInputExpressionRequirement:  dump_requirement,
        cwl.WorkflowStep:                    dump_step
    }
    # print(f" >>>>>>>>>>>>>>>>>>>> {type(obj)}")
    func = cwl_dumper_dict.get(type(obj), lambda: "Invalid")
    # print(f" >>>>>>>>>>>>>>>>>>>> {func}")
    return func(obj)


def create_workflow(obj, wfi):
    print(f"==== {type(obj)} ====")
    ins = get_wf_inputs(obj.inputs)
    outs = get_wf_outputs(obj.outputs)
    print(f"ins:  {ins}")
    print(f"outs: {outs}")
    # for i in obj.requirements:
    #     cwl_dumper(i)
    wfi.initialize_workflow(ins, outs)
#    get_wf_tasks(obj.steps)
    for i in obj.steps:
        cwl_dumper(i)


def get_wf_inputs(objarray):
    wf_inputs = set()
    for i in objarray:
        wf_inputs.add(i.id.split("#")[1])
    return wf_inputs


def get_wf_outputs(objarray):
    wf_outputs = set()
    for i in objarray:
        #wf_outputs.add(i.id.split("#")[1])
        wf_outputs.add(i.outputSource.split('#')[1])
    return wf_outputs


def dump_requirement(obj):
    print(f"---- {type(obj)} ----")
    print("    *** TBD")


def dump_step(obj):
    print(f"---- {type(obj)} ----")
    print(f"id:               #{obj.id.split('#')[1]}")
    # print(f"label:            {obj.label}")
    # print(f"doc:              {obj.doc}")
    # print(f"hints:            {obj.hints}")
    # print(f"requirements:     {obj.requirements}")
    # print(f"scatter:          {obj.scatter}")
    # print(f"scatterMethod:    {obj.scatterMethod}")
    # print(f"extension_fields: {obj.extension_fields}")
    for i in obj.in_:
        cwl_dumper(i)
    for i in obj.out:
        print(f"out:              #{i.split('#')[1]}")
    cwl_dumper(obj.run)


def dump_workflow_step_input(obj):
    print(f"---- {type(obj)} ----")
    print(f"id:               #{obj.id.split('#')[1]}")
    print(f"source:           #{obj.source.split('#')[1]}")
    # print(f"linkMerge:        {obj.linkMerge}")
    # print(f"default:          {obj.default}")
    # print(f"valueFrom:        {obj.valueFrom}")
    # print(f"extension_fields: {obj.extension_fields}")


def dump_command_line_tool(obj):
    print(f"---- {type(obj)} ----")
    print(f"id:                 {obj.id}")
    # print(f"label:              {obj.label}")
    # print(f"doc:                {obj.doc}")
    # print(f"hints:              {obj.hints}")
    # print(f"requirements:       {obj.requirements}")
    print(f"baseCommand:        {obj.baseCommand}")
    print(f"stdin:              {obj.stdin}")
    print(f"stdout:             {obj.stdout}")
    print(f"stderr:             {obj.stderr}")
    # print(f"arguments:          {obj.arguments}")
    # print(f"successCodes:       {obj.successCodes}")
    # print(f"temporaryFailCodes: {obj.temporaryFailCodes}")
    # print(f"permanentFailCodes: {obj.permanentFailCodes}")
    # print(f"extension_fields:   {obj.extension_fields}")
    for i in obj.inputs:
        cwl_dumper(i)
    for i in obj.outputs:
        cwl_dumper(i)


def dump_command_input_parameter(obj):
    print(f"---- {type(obj)} ----")
    print(f"id:               {obj.id}")
    # print(f"label:            {obj.label}")
    # print(f"doc:              {obj.doc}")
    # print(f"secondaryFiles:   {obj.secondaryFiles}")
    # print(f"streamable:       {obj.streamable}")
    # print(f"format:           {obj.format}")
    print(f"inputBinding:")
    cwl_dumper(obj.inputBinding)
    # print(f"default:          {obj.default}")
    print(f"type:             {obj.type}")
    # print(f"extension_fields: {obj.extension_fields}")


def dump_command_output_parameter(obj):
    print(f"---- {type(obj)} ----")
    print(f"id:               {obj.id}")
    # print(f"label:            {obj.label}")
    # print(f"doc:              {obj.doc}")
    # print(f"secondaryFiles:   {obj.secondaryFiles}")
    # print(f"streamable:       {obj.streamable}")
    # print(f"format:           {obj.format}")
    #print(f"outputBinding:")
    #cwl_dumper(obj.inputBinding)
    # print(f"default:          {obj.default}")
    print(f"type:             {obj.type}")


def dump_command_line_binding(obj):
    print(f"---- {type(obj)} ----")
    # print(f"loadContents:     {obj.loadContents}")
    print(f"position:         {obj.position}")
    # print(f"prefix:           {obj.prefix}")
    # print(f"sepatate:         {obj.separate}")
    # print(f"itemSeparator:    {obj.itemSeparator}")
    # print(f"shellQuote:       {obj.shellQuote}")
    # print(f"extension_fields: {obj.extension_fields}")





def parse_args(args=sys.argv[1:]):
    """Parse arguments."""
    parser = argparse.ArgumentParser(description=sys.modules[__name__].__doc__)

    parser.add_argument("cwl_file", type=str, help="CWL file dump")
    return parser.parse_args(args)


def main():
    args = parse_args()
    # Open the database using default parameters. You'll obviously need one
    # running at the default port. See the documentation on the internal BEE
    # GitLab for instructions on how to o this:
    #
    # https://gitlab.lanl.gov/BEE/database/neo4j
    wfi = WorkflowInterface()
    top = cwl.load_document(args.cwl_file)
    create_workflow(top, wfi)
    # Clear the workflow that we just built from the database. Comment out if you
    # want to take a look at the workflow in the database. Note that if this code
    # dies with an error before it gets here you'll have to delete the databse via
    # Cypher in the wen interface. This command will do the trick:
    #
    # MATCH(n) WITH n LIMIT 10000 DETACH DELETE n
    wfi.finalize_workflow()


if __name__ == "__main__":
    sys.exit(main())
