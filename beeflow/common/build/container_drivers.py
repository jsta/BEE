"""Container build driver.

All container-based build systems belong here.
"""

from abc import ABC
import os
from beeflow.common.config.config_driver import BeeConfig
# from beeflow.common.crt.crt_drivers import CharliecloudDriver, SingularityDriver


class ContainerBuildDriver(ABC):
    """Driver interface between WFM and a container build system.

    A driver object must implement an __init__ method that
    requests a RTE, and a method to return the requested RTE.
    """


class CharliecloudBuildDriver(ContainerBuildDriver):
    """Driver interface between WFM and a container build system.

    A driver object must implement an __init__ method that
    requests a RTE, and a method to return the requested RTE.
    """

    def __init__(self, task, userconf_file=None):
        """Begin build request.

        Parse hints and requirements to determine target build
        system. Harvest relevant BeeConfig params in kwargs.

        :param requirements: the workflow requirements
        :type requirements: set of Requirement instances
        :param hints: the workflow hints (optional requirements)
        :type hints: set of Requirement instances
        :param kwargs: Dictionary of build system config options
        :type kwargs: set of build system parameters
        """
        if userconf_file:
            bc = BeeConfig(userconfig=userconf_file)
        else:
            bc = BeeConfig()
        try:
            if bc.userconfig['DEFAULT'].get('bee_workdir'):
                build_dir = '/'.join([bc.userconfig['DEFAULT'].get('bee_workdir'),
                                     'build_scratch'])
            else:
                print('Invalid config file. bee_workdir not found in DEFAULT.')
                print('Assuming bee_workdir is ~/.beeflow')
                build_dir = '~/.beeflow/build_scratch'
        except KeyError:
            print('Invalid config file. DEFAULT section missing.')
            print('Assuming bee_workdir is ~/.beeflow')
            build_dir = '~/.beeflow/build_scratch'
        finally:
            self.build_dir = bc.resolve_path(build_dir)
            os.makedirs(self.build_dir, exist_ok=True)
        self.task = task

    def parse_build_config(self):
        """Parse bc_options to separate BeeConfig and CWL concerns.

        bc_options is used to receive an unknown number of parameters.
        both BeeConfig and CWL files may have options required for
        the build service. Parse and store them.
        """
        print('Charliecloud, parse_build_config:', self, '.')

    def validate_build_config(self):
        """Ensure valid config.

        Parse bc_options to ensure BeeConfig options are compatible
        with CWL specs.
        """
        print('Charliecloud, validate_build_config:', self, '.')

    def build(self):
        """Build RTE as configured.

        Build the RTE based on a validated configuration.
        """
        print('Charliecloud, validate_build_config:', self, '.')

    def validate_build(self):
        """Validate RTE.

        Confirm build procedure completed successfully.
        """
        print('Charliecloud, validate_build:', self, '.')

    def dockerPull(self, path, kwargs):
        """CWL compliant dockerPull.

        CWL spec 09-23-2020: Specify a Docker image to
        retrieve using docker pull. Can contain the immutable
        digest to ensure an exact container is used.
        """

    def dockerLoad(self):
        """CWL compliant dockerLoad.

        CWL spec 09-23-2020: Specify a HTTP URL from which to
        download a Docker image using docker load.
        """

    def dockerFile(self):
        """CWL compliant dockerFile.

        CWL spec 09-23-2020: Supply the contents of a Dockerfile
        which will be built using docker build.
        """

    def dockerImport(self):
        """CWL compliant dockerImport.

        CWL spec 09-23-2020: Provide HTTP URL to download and
        gunzip a Docker images using docker import.
        """

    def dockerImageId(self):
        """CWL compliant dockerImageId.

        CWL spec 09-23-2020: The image id that will be used for
        docker run. May be a human-readable image name or the
        image identifier hash. May be skipped if dockerPull is
        specified, in which case the dockerPull image id must be
        used.
        """

    def dockerOutputDirectory(self):
        """CWL compliant dockerOutputDirectory.

        CWL spec 09-23-2020: Set the designated output directory
        to a specific location inside the Docker container.
        """


class SingularityBuildDriver(ContainerBuildDriver):
    """Driver interface between WFM and a container build system.

    A driver object must implement an __init__ method that
    requests a RTE, and a method to return the requested RTE.
    """

    def initialize_builder(self, requirements, hints, bc_options):
        """Begin build request.

        Parse hints and requirements to determine target build
        system. Harvest relevant BeeConfig params in bc_options.

        :param requirements: the workflow requirements
        :type requirements: set of Requirement instances
        :param hints: the workflow hints (optional requirements)
        :type hints: set of Requirement instances
        :param bc_options: Dictionary of build system config options
        :type bc_options: set of build system parameters
        """
        print('Singularity, initialize_builder:', self, requirements, hints, bc_options, '.')

    def parse_build_config(self):
        """Parse bc_options to separate BeeConfig and CWL concerns.

        bc_options is used to receive an unknown number of parameters.
        both BeeConfig and CWL files may have options required for
        the build service. Parse and store them.
        """
        print('Singularity, parse_build_config:', self, '.')

    def validate_build_config(self):
        """Ensure valid config.

        Parse bc_options to ensure BeeConfig options are compatible
        with CWL specs.
        """
        print('Singularity, validate_build_config:', self, '.')

    def build(self):
        """Build RTE as configured.

        Build the RTE based on a validated configuration.
        """
        print('Singularity, validate_build_config:', self, '.')

    def validate_build(self):
        """Validate RTE.

        Confirm build procedure completed successfully.
        """
        print('Singularity, validate_build:', self, '.')

    def dockerPull(self):
        """CWL compliant dockerPull.

        CWL spec 09-23-2020: Specify a Docker image to
        retrieve using docker pull. Can contain the immutable
        digest to ensure an exact container is used.
        """

    def dockerLoad(self):
        """CWL compliant dockerLoad.

        CWL spec 09-23-2020: Specify a HTTP URL from which to
        download a Docker image using docker load.
        """

    def dockerFile(self):
        """CWL compliant dockerFile.

        CWL spec 09-23-2020: Supply the contents of a Dockerfile
        which will be built using docker build.
        """

    def dockerImport(self):
        """CWL compliant dockerImport.

        CWL spec 09-23-2020: Provide HTTP URL to download and
        gunzip a Docker images using docker import.
        """

    def dockerImageId(self):
        """CWL compliant dockerImageId.

        CWL spec 09-23-2020: The image id that will be used for
        docker run. May be a human-readable image name or the
        image identifier hash. May be skipped if dockerPull is
        specified, in which case the dockerPull image id must be
        used.
        """

    def dockerOutputDirectory(self):
        """CWL compliant dockerOutputDirectory.

        CWL spec 09-23-2020: Set the designated output directory
        to a specific location inside the Docker container.
        """
# Ignore snake_case requirement to enable CWL compliant names.
# pylama:ignore=C0103
