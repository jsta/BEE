import os
import subprocess

from docker import Docker
from termcolor import colored, cprint
from threading import Thread
from threading import Event
from bee_task import BeeTask

from keystoneauth1 import loading
from keystoneauth1 import session
from keystoneauth1.identity import v2

from glanceclient import Client as glanceClient
from novaclient.client import Client as novaClient
from neutronclient.v2_0.client import Client as neutronClient

class BeeOSLauncher(BeeTask):

    def __init__(self, task_id, beefile):

        BeeTask.__init__(self)
        # User configuration
        self.__task_conf = beefile['task_conf']
        self.__bee_os_conf = beefile['exec_env_conf']['bee_os']
        self.__docker_conf = beefile['docker_conf']
        self.__task_name = self.__task_conf['task_name']
        self.__task_id = task_id

        # Authentication
        # auth = v2.Password(username = os.environ['OS_USERNAME'], 
        #                    password = os.environ['OS_PASSWORD'], 
        #                    tenant_name = os.environ['OS_TENANT_NAME'], 
        #                    auth_url = os.environ['OS_AUTH_URL'])

        # auth = v2.Password(username = 'cjy7117',
        #            password = 'Wait4aTrain7!',
        #            tenant_name = 'CH-819321',
        #            auth_url = 'https://chi.tacc.chameleoncloud.org:5000/v2.0')
        
        # self.session = session.Session(auth = auth)
        
        # self.glance = glanceClient('2', session = self.session)

        # self.nova = novaClient('2', session = self.session)

        # self.neutron = neutronClient(session = self.session)



    def run(self):
        self.launch()


    def launch(self):


        #f = open(expanduser("~") + '/.bee/ssh_key/id_rsa.pub','r')
        #publickey = f.readline()[:-1]
        #keypair = nova.keypairs.create('bee-key', publickey)
        #f.close()


        # flavors = self.nova.flavors.list()
        # print (flavors)
        # f = flavors[0]

        #images = self.glance.images.list()
        #for image in images:
        #   print image

        # i = self.glance.images.get('10c1c632-1c4d-4c9d-bdd8-7938eeba9f14')

        # print(i)
        # #k = self.nova.keypairs.create(name = 'bee-key')        

        # self.nova.servers.create(name = 'bee-os',
        #                          images = i,
        #                          flavor = f,
        #                          scheduler_hints = {'reservation': 'ac2cd341-cf88-4238-b45a-50fab07de465'},
        #                          key_name = 'bee-key'
        #                          )


        

    def launch_stack(self):
        curr_dir = os.path.dirname(os.path.abspath(__file__))
        hot_template_dir = curr_dir + "/bee_hot"
        exec_cmd = ["stack",
                    "create -t {}".format(hot_template_dir),
                    "--parameter nfs_client_count={}".format(self.__bee_os_conf['num_of_nodes']),
                    "--parameter key_name=bee-key",
                    "--parameter reservation_id=04a7505e-6b16-4cbd-90d4-0a8b32aeed0f teststack"]

