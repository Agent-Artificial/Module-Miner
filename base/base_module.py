import os
import base64
import requests
import subprocess
from pydantic import BaseModel
from pathlib import Path
from typing import Optional


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
        
        
if __name__ == "__main__":
    module_settings = ModuleConfig(
        module_name="embedding",
        module_path="modules/embedding",
        module_url="https://registrar-cellium.ngrok.app",
        module_endpoint="/modules/embedding"
    )                
    module = BaseModule(module_settings)