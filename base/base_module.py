import os
import base64
import requests
import subprocess
from loguru import logger
from pydantic import BaseModel, Field
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv


load_dotenv()   


class ModuleConfig(BaseModel):
    module_name: Optional[str] = None
    module_path: Optional[str] = None
    module_endpoint: Optional[str] = None
    module_url: Optional[str] = None


class BaseModule(BaseModel):
    module_config: Optional[ModuleConfig] = Field(default_factory=ModuleConfig)  # None

    def __init__(
        self,
        module_config: Optional[ModuleConfig] = ModuleConfig(
            module_path=os.getenv("MODULE_PATH"),
            module_name=os.getenv("MODULE_NAME"),
            module_url=os.getenv("MODULE_URL"),
            module_endpoint=os.getenv("MODULE_ENDPOINTS"),
        ),
    ):

        super().__init__(module_config=module_config.model_dump())
        self.module_config = module_config

    def init_module(self):
        logger.debug(f"Module path: {self.module_config.module_path}")
        self.install_module(self.module_config)
        return self.module_config

    def _check_and_prompt(self, path: Path, message: str) -> Optional[str]:
        if path.exists():
            content = path.read_text(encoding="utf-8")
            print(content)
            user_input = input(f"{message} Do you want to overwrite it? (y/n) ").lower()
            return None if user_input in ["y", "yes"] else content
        return None

    def check_public_key(self) -> Optional[str]:
        public_key_path = Path("data/public_key.pub")
        return self._check_and_prompt(public_key_path, "Public key exists.")

    def get_public_key(
        self, key_name: str = "public_key", public_key_path: str = "data/public_key.pem"
    ):
        public_key = requests.get(
            f"{self.module_config.module_url}/modules/{key_name}", timeout=30
        ).text
        os.makedirs("data", exist_ok=True)
        existing_key = self.check_public_key()
        if existing_key is None:
            Path(public_key_path).write_text(public_key, encoding="utf-8")
        return existing_key or public_key

    def check_for_existing_module(self) -> Optional[str]:
        module_setup_path = Path(
            f"{self.module_config.module_path}/setup_{self.module_config.module_name}.py"
        )
        return self._check_and_prompt(module_setup_path, "Module exists.")

    def request_module(self):
        module=None
        try:
            module = requests.get(
                f"{self.module_config.module_url}{self.module_config.module_endpoint}",
                timeout=30,
            ).text
        except Exception as e:
            logger.error(f"Error downloading module: {e}")
        os.makedirs("modules", exist_ok=True)

        module_setup_path = Path(
            f"{self.module_config.module_path}/setup_{self.module_config.module_name}.py"
        )


        os.makedirs(self.module_config.module_path, exist_ok=True)
        unencoded = base64.b64decode(module).decode("utf-8")
        module_setup_path.write_text(unencoded, encoding="utf-8")
        return module

    def remove_module(self, module_path):
        Path(module_path).rmdir()

    def save_module(self, module_data: str):
        Path(
            f"{self.module_config.module_path}/setup_{self.module_config.module_name}.py"
        ).write_text(module_data, encoding="utf-8")

    def setup_module(self):
        subprocess.run(
            f"python {self.module_config.module_path}/setup_{self.module_config.module_name}.py",
            shell=True,
            check=True,
        )

    def update_module(self, module_config: ModuleConfig):
        self.install_module(module_config=module_config)

    def install_module(self, module_config: ModuleConfig):
        self.module_config = module_config
        self.request_module()
        self.setup_module()
        install_path = Path(f"modules/{self.module_config.module_name}/install_{self.module_config.module_name}.sh")
        install_path.chmod(0o755)
        
        subprocess.run(
            ["bash", f"{install_path}"],
            shell=True,
            check=True,
        )


module = BaseModule()
