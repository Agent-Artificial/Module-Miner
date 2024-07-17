import bittensor
from pydantic import BaseModel
from typing import List, Union, Any, Callable
from chains.tao.axons.protocol import ModuleRequest
from bittensor.subnets import SubnetsAPI
from chains.tao.utils.btcli_functions import app, create_command_endpoint, create_endpoint
from data_models import MinerRequest, BaseModule


class Process(BaseModel):
    process: Callable[..., Any]


class ModuleAxon(SubnetsAPI):
    def __init__(self, wallet: bittensor.wallet):
        super().__init__(wallet)
        self.netuid = 1
        self.name = "test_miner_hot"
        self.module = None
        self.process = None
        self.available_commands = []
        
    def create_command_endpoint(self, path, command_name: str, command_class: Process):
        self.available_commands.append(command_name)
        create_command_endpoint(path, command_name=command_name, command_class=command_class)
        
    def create_endpoint(self, path, command_info):
        create_endpoint(path, command_info)
        
    def prepare_synapse(self, *args, **kwargs) -> Any:
        ModuleRequest(request_input=MinerRequest(*args, **kwargs))

    def process_responses(self, responses: List[Any]) -> Any:
        full_response = None
        for response in responses:
            full_response += response
        return full_response

    def set_module(self, module: BaseModule):
        self.module = module
        
    def set_process(self, module: BaseModule):
        self.process = Process(process=module.process)