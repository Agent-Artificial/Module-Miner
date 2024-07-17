from subnet_template.neurons.miner import BaseMinerNeuron

from chains.tao.neurons.config import get_config, Config
from chains.tao.axons.axon import ModuleAxon, Process, ModuleRequest
from base.base_module import BaseModule

default_config = get_config(is_miner=True, use_cli=False)


class TAOMiner(BaseMinerNeuron):
    def __init__(self, config: Config):
        super().__init__(config)
        self.config = config
        self.axon = ModuleAxon(config.wallet)
        
    def set_module(self, module: BaseModule):
        self.axon.set_module(module)
        
    async def forward(self, module_request: ModuleRequest):
        return self.axon.process(module_request)
    
    def set_process(self, module: BaseModule):
        self.axon.set_process(module)
        
        
        
