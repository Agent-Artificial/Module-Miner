import os
import torch
import json
import requests
import base64
import subprocess
from pathlib import Path
from loguru import logger
from pydantic import BaseModel, Field
from typing import Dict, Union, Optional, Any, List
from abc import ABC, abstractmethod
from fastapi import APIRouter, FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from substrateinterface.keypair import Keypair


app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.mount("/in", StaticFiles(directory="modules/translation/in"), name="in")
app.mount("/out", StaticFiles(directory="modules/translation/out"), name="out")

TASK_STRINGS = {
    "speech2text": "s2tt",
    "speech2speech": "s2st",
    "auto_speech_recognition": "asr",
    "text2speech": "t2st",
    "text2text": "t2tt",
}

TARGET_LANGUAGES = {
    "English": "eng",
    "Afrikaans": "afr",
    "Amharic": "amh",
    "Modern Standard Arabic": "arb",
    "Moroccan Arabic": "ary",
    "Egyptian Arabic": "arz",
    "Assamese": "asm",
    "Asturian": "ast",
    "North Azerbaijani": "azj",
    "Belarusian": "bel",
    "Bengali": "ben",
    "Bosnian": "bos",
    "Bulgarian": "bul",
    "Catalan": "cat",
    "Cebuano": "ceb",
    "Czech": "ces",
    "Central": "ckb",
    "Mandarin Chinese": "cmn",
    "Mandarin Chinese Hant": "cmn_Hant",
    "Welsh": "cym",
    "Danish": "dan",
    "German": "deu",
    "Estonian": "est",
    "Basque": "eus",
    "Finnish": "fin",
    "French": "fra",
    "Nigerian Fulfulde": "fuv",
    "West Central Oromo": "gaz",
    "Irish": "gle",
    "Galician": "glg",
    "Gujarati": "guj",
    "Hebrew": "heb",
    "Hindi": "hin",
    "Croatian": "hrv",
    "Hungarian": "hun",
    "Armenian": "hye",
    "Igbo": "ibo",
    "Indonesian": "ind",
    "Icelandic": "isl",
    "Italian": "ita",
    "Javanese": "jav",
    "Japanese": "jpn",
    "Kamba": "kam",
    "Kannada": "kan",
    "Georgian": "kat",
    "Kazakh": "kaz",
    "Kabuverdianu": "kea",
    "Halh Mongolian": "khk",
    "Khmer": "khm",
    "Kyrgyz": "kir",
    "Korean": "kor",
    "Lao": "lao",
    "Lithuanian": "lit",
    "Luxembourgish": "ltz",
    "Ganda": "lug",
    "Luo": "luo",
    "Standard Latvian": "lvs",
    "Maithili": "mai",
    "Malayalam": "mal",
    "Marathi": "mar",
    "Macedonian": "mkd",
    "Maltese": "mlt",
    "Meitei": "mni",
    "Burmese": "mya",
    "Dutch": "nld",
    "Norwegian Nynorsk": "nno",
    "Norwegian Bokmål": "nob",
    "Nepali": "npi",
    "Nyanja": "nya",
    "Occitan": "oci",
    "Odia": "ory",
    "Punjabi": "pan",
    "Southern Pashto": "pbt",
    "Western Persian": "pes",
    "Polish": "pol",
    "Portuguese": "por",
    "Romanian": "ron",
    "Russian": "rus",
    "Slovak": "slk",
    "Slovenian": "slv",
    "Shona": "sna",
    "Sindhi": "snd",
    "Somali": "som",
    "Spanish": "spa",
    "Serbian": "srp",
    "Swedish": "swe",
    "Swahili": "swh",
    "Tamil": "tam",
    "Telugu": "tel",
    "Tajik": "tgk",
    "Tagalog": "tgl",
    "Thai": "tha",
    "Turkish": "tur",
    "Ukrainian": "ukr",
    "Urdu": "urd",
    "Northern Uzbek": "uzn",
    "Vietnamese": "vie",
    "Xhosa": "xho",
    "Yoruba": "yor",
    "Cantonese": "yue",
    "Colloquial Malay": "zlm",
    "Standard Malay": "zsm",
    "Zulu": "zul",
}


class ModuleConfig(BaseModel):
    module_name: Optional[str] = None
    module_path: Optional[str] = None
    module_endpoint: Optional[str] = None
    module_url: Optional[str] = None


class BaseModule(BaseModel):
    module_config: Optional[ModuleConfig] = None
    
    def __init__(self, module_config: ModuleConfig):
        super().__init__(module_config=module_config)
        self.module_config = module_config
        self.init_module()
        
    def init_module(self):
        if not os.path.exists(self.module_config.module_path):
            os.makedirs(self.module_config.module_path)
            self.install_module(self.module_config)
        
    def _check_and_prompt(self, path: Path, message: str) -> Optional[str]:
        if path.exists():
            content = path.read_text(encoding="utf-8")
            print(content)
            user_input = input(f"{message} Do you want to overwrite it? (y/n) ").lower()
            return None if user_input in ['y', 'yes'] else content
        return None

    def check_public_key(self) -> Optional[str]:
        public_key_path = Path("data/public_key.pub")
        return self._check_and_prompt(public_key_path, "Public key exists.")

    def get_public_key(self, key_name: str = "public_key", public_key_path: str = "data/public_key.pem"):
        public_key = requests.get(f"{self.module_config.module_url}/modules/{key_name}", timeout=30).text
        os.makedirs("data", exist_ok=True)
        existing_key = self.check_public_key()
        if existing_key is None:
            Path(public_key_path).write_text(public_key, encoding="utf-8")
        return existing_key or public_key
        
    def check_for_existing_module(self) -> Optional[str]:
        module_setup_path = Path(f"{self.module_config.module_path}/setup_{self.module_config.module_name}.py")
        return self._check_and_prompt(module_setup_path, "Module exists.")
                
    def get_module(self):
        module = requests.get(f"{self.module_config.module_url}{self.module_config.module_endpoint}", timeout=30).text
        os.makedirs("modules", exist_ok=True)
        
        module_setup_path = Path(f"{self.module_config.module_path}/setup_{self.module_config.module_name}.py")
        existing_module = self.check_for_existing_module()
        
        if existing_module is None:
            os.makedirs(self.module_config.module_path, exist_ok=True)
            module_setup_path.write_text(module, encoding="utf-8")
        return existing_module or module

    def remove_module(self):
        Path(self.module_config.module_path).rmdir()
        
    def save_module(self, module_data: str):
        Path(f"{self.module_config.module_path}/setup_{self.module_config.module_name}.py").write_text(module_data, encoding="utf-8")

    def setup_module(self):
        subprocess.run(f"python {self.module_config.module_path}/setup_{self.module_config.module_name}.py", shell=True, check=True)

    def update_module(self, module_config: ModuleConfig):
        self.install_module(module_config=module_config)

    def install_module(self, module_config: ModuleConfig):
        self.module_config = module_config
        self.get_module()
        self.setup_module()        
        subprocess.run(f"bash {self.module_config.module_path}/install_{self.module_config.module_name}.sh", shell=True, check=True)
       

class TranslationConfig(BaseModel):
    model_name_or_card: Union[str, Any] = "facebook/seamless-M4T-V2-large"
    vocoder_name: str = (
        "vocoder_v2"
        if model_name_or_card == "facebook/seamless-M4T-V2-large"
        else "vocoder_36langs"
    )
    device: Any = torch.device(device="cuda:0")
    text_tokenizer: str = model_name_or_card
    apply_mintox: bool = (True,)
    dtype: Any = (torch.float16,)
    input_modality: Optional[Any] = (None,)
    output_modality: Optional[Any] = None


class MinerRequest(BaseModel):
    data: Optional[Any] = None
    
    
class TranslationData(BaseModel):
    input: str
    task_string: str
    source_language: Optional[str] = None
    target_language: str
    
    
class TranslationRequest(MinerRequest):
    def __init__(self, data: TranslationData):
        super().__init__()
        self.data = data


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
            try:
                logger.debug(request.data["input"][0:30])
                logger.debug(request.data["task_string"])
                logger.debug(request.data["source_language"])
                logger.debug(request.data["target_language"])
                res = self.process(request)
                return res
            except Exception as e:
                logger.error(e)
                return {"error": str(e)}
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
    def process(self, request: Request) -> Any:
        """Process a request made to the module."""     
