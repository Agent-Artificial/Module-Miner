import os
from dotenv import load_dotenv
from data_models import MinerConfig
from base.base_miner import BaseMiner

load_dotenv()



miner_config = MinerConfig(
    miner_name=os.getenv("MINER_NAME"),
    miner_keypath=os.getenv("KEYPATH_NAME"),
    miner_host=os.getenv("MINER_HOST"),
    external_address=os.getenv("EXTERNAL_ADDRESS"),
    miner_port=os.getenv("MINER_PORT"),
    stake=os.getenv("STAKE"),
    netuid=os.getenv("NETUID"),
    funding_key=os.getenv("FUNDING_KEY"),
    funding_modifier=os.getenv("MODIFIER"),
    module_name=os.getenv("MODULE_NAME")
)


class MinerManager:
    miner_configs: Dict[str, Any]
    miner_config: Dict[str, Any]
    