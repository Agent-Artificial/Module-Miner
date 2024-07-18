import uvicorn
from fastapi import FastAPI

from subnet_template.neurons.miner import BaseMinerNeuron

from chains.tao.neurons.config import get_config
from chains.tao.axons.axon import ModuleAxon, Process, ModuleRequest
from base.base_module import BaseModule

default_config = get_config()


class TAOMiner(BaseMinerNeuron):
    def __init__(self, config: default_config = default_config):
        super().__init__(config)
        self.config = config
        self.axon = ModuleAxon(config.wallet)
        
    def set_module(self, module: BaseModule):
        self.axon.set_module(module)
        
    async def forward(self, module_request: ModuleRequest):
        return self.axon.process(module_request)
    
    def set_process(self, module: BaseModule):
        self.axon.set_process(module)
        
    def serve_module(self, app: FastAPI):
        self.axon.serve_modules(app)
    
    def cli_command(self, **kwargs):
        commands = {
            "wallet":["btcli", "wallet", f"{kwargs['command']}", "--wallet.name", f"{kwargs['wallet_name']}", "--subtensor.chain_endpoint", "ws://127.0.0.1:9946"],
            "subnet": ["btcli", "subnet", f"{kwargs['command']}", "--wallet.name", f"{kwargs['wallet_name']}", "--wallet.hotkey", f"{kwargs['hotkey']}", "--subtensor.chain_endpoint", "ws://127.0.0.1:9946"]
            }
    
    def get_cli_commands(self):
        return ["wallet", "subnet"]
        
