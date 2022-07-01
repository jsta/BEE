# BEE: Build and Execute Environment
BEE is a workflow orchestration system designed to build containerized HPC applications and orchestrate workflows across HPC and cloud systems. BEE has adopted the Common Workflow Language ([CWL](https://www.commonwl.org/)) for specifying workflows.

BEE workflows can be archived for provenance and reproducibility. BEE can orchestrate workflows with containerized applications or those built locally on a system. There are advantages to containerizing an application.

A container is a package of code (usually binaries) and all of that code's dependencies (libraries, etc.). Once built, this container can be run on many different platforms.
Containers provide many benefits:

- Users can choose their own software stack (libraries, compilers, etc.) and
not be bound by the currently installed environment on any one machine.
- Codes can be run portably across numerous platforms--all dependencies will be
downloaded and installed at run time.
- Entire _workflow_ environments can be built into one or more containers. A user
can include visualization and analysis tools along with the application. They
will all work together as the application runs.
- Provenance and history can be tracked by storing containers in a historical
repository. At any time, an older container can be rerun (all of its
dependencies are stored with it). Execution is repeatable and interactions
between software components can be tracked.
- Functional testing can be performed on smaller, dissimilar machines--there is
no real need to test on the actual HPC platform (performance testing obviously
requires target hardware).






# Contributing

The BEE project adheres to style guidelines specified in `./setup.cfg`. Before attempting to commit and push changes, please install our pre-commit githooks by running the following command in project root:
If using `git --version` >= 2.9
```
git config core.hooksPath .githooks
```
Otherwise
```
cp .githooks/* .git/hooks/
```
Using these git hooks will ensure your contributions adhere to style guidelines required for contribution. You will need to repeat these steps for every `BEE_Private` repo you clone.

# Mail List and Contact

For bugs and problems report, suggestions and other general questions regarding the BEE project, email questions to [bee-dev@lanl.gov](bee-dev@lanl.gov). 


# Release

This software has been approved for open source release and has been assigned **BEE C17056**.


# Publications

- BEE Orchestrator: Running Complex Scientific Workflows on Multiple Systems, HiPC, 2021, [DOI: 10.1109/HiPC53243.2021.00052](https://doi.org/10.1109/HiPC53243.2021.00052)
- "BeeSwarm: Enabling Parallel Scaling Performance Measurement in Continuous Integration for HPC Applications", ASE, 2021, [DOI: 10.1109/ASE51524.2021.9678805](https://www.computer.org/csdl/proceedings-article/ase/2021/033700b136/1AjTjgnW2pa#:~:text=10.1109/ASE51524.2021.9678805)
- "BeeFlow: A Workflow Management System for In Situ Processing across HPC and Cloud Systems", ICDCS, 2018, [DOI: 10.1109/ICDCS.2018.00103](https://ieeexplore.ieee.org/abstract/document/8416366)
- "Build and execution environment (BEE): an encapsulated environment enabling HPC applications running everywhere", IEEE BigData, 2018, [DOI: 10.1109/BigData.2018.8622572](https://ieeexplore.ieee.org/document/8622572)

# Copyright
License can be found [here](https://github.com/lanl/BEE/blob/master/LICENSE)
=======
