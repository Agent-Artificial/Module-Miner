import json
import subprocess
from pathlib import Path
from loguru import logger
from abc import ABC, abstractmethod
from typing import Dict, Optional, Any, List
from pydantic import BaseModel
from fastapi import  APIRouter
from communex.client import CommuneClient
from communex._common import get_node_url
from communex.compat.key import Keypair
from base.base_module import ModuleConfig

comx = CommuneClient(get_node_url())


class MinerRequest(BaseModel):
    data: Optional[Any] = None


class MinerConfig(BaseModel):
    miner_name: Optional[str] = None
    miner_keypath: Optional[str] = None
    miner_host: Optional[str] = None
    external_address: Optional[str] = None
    miner_port: Optional[int] = None
    stake: Optional[float] = None
    netuid: Optional[int] = None
    funding_key: Optional[str] = None
    funding_modifier: Optional[float] = None
    module_name: Optional[str] = None
        

class BaseMiner(ABC):
    module_config: Optional[ModuleConfig] = None
    module_configs: Optional[List[MinerConfig]] = []
    miner_key_dict: Optional[Dict[str, Any]] = {}
    key_name: Optional[str] = None
    miners: Optional[Dict[str, Any]] = {}
    router: Optional[APIRouter] = None
    
    def __init__(self, module_config: ModuleConfig, miner_config: MinerConfig):
        self.module_config = module_config
        self.miner_config = miner_config
        self.module_configs = self._load_configs("modules/module_configs.json")
        self.miner_configs = self._load_configs("modules/miner_configs.json")
        self.miners = self._load_miner_keys()
        self.router = APIRouter()

    def _load_configs(self, file_path: str) -> List[Dict[str, Any]]:
        path = Path(file_path)
        if path.exists():
            return json.loads(path.read_text(encoding="utf-8"))
        configs = []
        path.write_text(json.dumps(configs, indent=4), encoding="utf-8")
        return configs

    def _load_miner_keys(self) -> Dict[str, Any]:
        key_path = Path("data/instance_data/miner_keys.json")
        if key_path.exists():
            return json.loads(key_path.read_text(encoding="utf-8"))
        
        self.miner_key_dict = {
            config["miner_name"]: json.loads(Path(config["miner_keypath"]).read_text(encoding="utf-8"))
            for config in self.miner_configs
            if Path(config["miner_keypath"]).exists()
        }
        
        key_path.write_text(json.dumps(self.miner_key_dict, indent=4), encoding="utf-8")
        return self.miner_key_dict

    def add_route(self, module_name: str):
        @self.router.post(f"/modules/{module_name}/process")
        def process_request(request: MinerRequest):
            return self.process(request)
        app.include_router(self.router)

    @staticmethod
    def run_server(host_address: str, port: int):
        import uvicorn
        uvicorn.run(app, host=host_address, port=port)

    def add_miner_key(self, key_name: str, miner_keypath: Path = Path("data/instance_data/miner_keys.json"), miner_config: Optional[MinerConfig] = None):
        if miner_config:
            self.miner_key_dict[key_name] = miner_config.model_dump()
        else:
            config = self._prompt_miner_config()
            self.miner_key_dict[key_name] = config.model_dump()
        
        self._save_miner_keys(miner_keypath)

    def _prompt_miner_config(self) -> MinerConfig:
        return MinerConfig(
            miner_name=input("Enter miner_name: "),
            miner_keypath=input("Enter miner_keypath [ex. $HOME/.commune/key/my_miner.json]: ") or None,
            miner_host=input("Enter miner_host [default 0.0.0.0]: ") or "0.0.0.0",
            external_address=input("Enter external_address: ") or None,
            miner_port=int(input("Enter miner_port [default 5757]: ") or 5757),
            stake=float(input("Enter stake [default 275COM]: ") or 275),
            netuid=int(input("Enter netuid [default 0]: ") or 0),
            funding_key=input("Enter funding_key: "),
            funding_modifier=float(input("Enter modifier [default 15COM]: ") or 15),
        )

    def remove_miner_key(self, key_name: str, miner_keypath: Path):
        self.miner_key_dict.pop(key_name, None)
        self._save_miner_keys(miner_keypath)

    def update_miner_key(self, key_name: str, miner_config: MinerConfig, miner_keypath: Path):
        self.miner_key_dict[key_name] = miner_config.model_dump()
        self._save_miner_keys(miner_keypath)

    def _save_miner_keys(self, miner_keypath: Path):
        miner_keypath.write_text(json.dumps(self.miner_key_dict, indent=4), encoding="utf-8")

    def get_keypair(self, key_name: str) -> Keypair:
        key_folder_path = Path(self.module_config.key_folder_path)
        json_data = json.loads((key_folder_path / f"{key_name}.json").read_text(encoding='utf-8'))["data"]
        key_data = json.loads(json_data)
        return Keypair(key_data["private_key"], key_data["public_key"], key_data["ss58_address"])

    def register_miner(self, miner_config: MinerConfig):
        command = f"bash modules/setup_miners.sh {miner_config.miner_name} {miner_config.miner_keypath} {miner_config.external_address} {miner_config.miner_port} {miner_config.stake} {miner_config.netuid} {miner_config.funding_key} {miner_config.funding_modifier}"
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        logger.info(result.stdout)
        logger.info(result.stderr)
        
    def serve_miner(self, miner_config: MinerConfig, register: bool = False):
        self.add_route(miner_config.module_name)
        if register:
            self.register_miner(miner_config)
            logger.info(f"Registered {miner_config.miner_name} at {miner_config.external_address}:{miner_config.miner_port}")
        self.run_server(miner_config.miner_host, miner_config.miner_port)

    @abstractmethod
    def process(self, miner_request: MinerRequest) -> Any:
        """Process a request made to the module."""