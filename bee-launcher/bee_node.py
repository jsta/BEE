# system
import os
import subprocess
from termcolor import cprint
# project
from host import Host


class BeeNode(object):
    def __init__(self, task_id, hostname, host, rank, task_conf,
                 shared_dir=None, user_name="beeuser"):
        # Basic configurations
        self.__status = ""
        self.__hostname = hostname
        self.rank = rank
        self.master = ""

        # Job configuration
        self.task_id = task_id
        self.task_conf = task_conf

        # Host machine
        self.host = Host(host)

        # Shared resourced
        self.shared_dir = shared_dir
        self.user_name = user_name

        # Output color list
        self.output_color_list = ["magenta", "cyan", "blue", "green",
                                  "red", "grey", "yellow"]
        self.output_color = "cyan"
        self.error_color = "red"

    @property
    def hostname(self):
        return self.__hostname

    @hostname.setter
    def hostname(self, h):
        cprint("[" + self.__hostname + "]: setting hostname to " + h,
               self.output_color)
        cmd = ["hostname", self.__hostname]
        self.root_run(cmd)

    @property
    def status(self):
        return self.__status

    @status.setter
    def status(self, status):
        cprint("[" + self.__hostname + "]: Setting status", self.output_color)
        self.__status = status

    # Run / CLI related functions
    def run(self, command, local_pfwd=None, remote_pfwd=None, async=False):
        # TODO: document
        #return self.host.run(command=command, local_pfwd=local_pfwd,
        #                     remote_pfwd=remote_pfwd, async=async)
	subprocess.call(command)	

    def root_run(self, command, local_pfwd=None, remote_pfwd=None, async=False):
        # TODO: document
        return self.host.run(command=command, local_pfwd=local_pfwd,
                             remote_pfwd=remote_pfwd, async=async)

    def parallel_run(self, command, local_pfwd=None, remote_pfwd=None,
                     async=False):
        pass

    # Task configuration run mode
    def general_run(self, script_path):
        cmd = ['sh', script_path]
        cprint("[" + self.__hostname + "] general run: " + str(cmd),
               self.output_color)
        self.run(cmd)

    # Directory / storage support functions
    def create_shared_dir(self):
        # Create directory
        # TODO: implement checks
        cprint("[" + self.__hostname + "]: create shared directory.",
               self.output_color)
        cmd = ["mkdir",
               "{}".format(self.shared_dir)]
        self.root_run(cmd)

    def update_ownership(self):
        # TODO: implement checks
        cprint("[" + self.__hostname + "]: update ownership of shared directory.",
               self.output_color)
        cmd = ["chown",
               "-R",
               "{}:{}".format(self.user_name, self.user_name),
               "{}".format(self.shared_dir)]
        self.root_run(cmd)

    def update_uid(self):
        cprint("[" + self.__hostname + "]: update user UID.", self.output_color)
        # Change user's UID to match host's UID.
        # This is necessary for dir sharing.
        cmd = ["usermod",
               "-u {} {}".format(os.getuid(), self.user_name)]

        self.root_run(cmd)

    def update_gid(self):
        cprint("[" + self.__hostname + "]: update user GID.", self.output_color)
        # Change user's GID to match host's GID.
        # This is necessary for dir sharing.
        cmd = ["groupmod",
               "-g {} {}".format(os.getgid(), self.user_name)]

        self.root_run(cmd)

    # Bee launching / management related functions
    def start(self):
        pass

    def checkpoint(self):
        pass

    def restore(self):
        pass

    def kill(self):
        pass
