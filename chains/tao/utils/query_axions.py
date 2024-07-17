import random
import numpy as np
import bittensor
from typing import List
from fastapi import HTTPException
from bittensor.axon import axon
from bittensor.metagraph import metagraph
from bittensor.dendrite import dendrite
from bittensor.synapse import Synapse




async def ping_uids(input_dendrite: dendrite, input_metagraph: metagraph, input_uids: List[int], timeout: int=30):
    axons = [input_metagraph.axons[uid] for uid in input_uids]
    try:
        response = await dendrite(
            timeout=timeout,
            dendrite=input_dendrite
        )
    except HTTPException as e:
        response = {"error": str(e), "message": f"Unable to query axons. {input_uids}", "status_code": e.status_code}

    return response

    