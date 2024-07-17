import json
import bittensor 
from fastapi import Response
from data_models import MinerRequest


class ModuleRequest(bittensor.Synapse):
    request_input: MinerRequest
    response_output: Response
    
    def deserialize(self) -> bittensor.Synapse:
        json.dumps(self.response_output.content)
    
    def serialize(self) -> bittensor.Synapse:
        json.loads(self.response_output.content)