import os
import json
import subprocess
from loguru import logger
from pydantic import BaseModel, Field
from typing import Dict, Any, List, Optional
from base.base_module import BaseModule
from data_models import  ModuleConfig
from importlib import import_module
from dotenv import load_dotenv

load_dotenv()




class ModuleManager:
    modules: Dict[str, Any]
    active_modules: Dict[str, Any]
    module_configs: Dict[str, Any]
    module_config: Dict[str, Any]
    module_name: str
    
    def __init__(self, module_name: Optional[str] = "translation"):
        self.modules = {}
        self.active_modules = {}
        self.module_name = module_name
        self.module_config = None
        self.module_configs = {}
        self.load_config(module_name)
    def load_config(self, module_name: str):
        if not self.module_configs:
            with open("data/instance_data/module_configs.json", "w", encoding="utf-8") as f:
                f.write("{}")
        with open("data/instance_data/module_configs.json", "r", encoding="utf-8") as f:
            self.module_configs = json.loads(f.read())
        if module_name in self.module_configs.keys():
            self.module_config = ModuleConfig(**self.module_configs[module_name])
            return self.module_config
        else:
            return self.add_module(module_name)
            
    def add_module(self, module_name: Optional[str] = None):
        if module_name is None:
            self.module_name = input("Enter the name of the module: ")
        self.module_config = ModuleConfig(
            module_name=self.module_name,
            module_path=f"modules/{self.module_name}",
            module_endpoint=f"/modules/{self.module_name}",
            module_url="http://localhost:4267"
        )
        if not self.module_configs:
            self.module_configs = {}
        self.module_configs[self.module_name] = self.module_config.model_dump()
 
        with open("data/instance_data/module_configs.json", "w", encoding="utf-8") as f:
            f.write(json.dumps(self.module_configs, indent=4))
        return self.module_config
    
    def install_module(self, module_config: ModuleConfig):
        if isinstance(module_config, dict):
            self.module_config = ModuleConfig(**module_config)
        if not os.path.exists(module_config.module_path):
            os.makedirs(module_config.module_path)
        module = BaseModule(module_config=self.module_config)
        module.init_module()
        self.active_modules[module_config.module_name] = module
        return module
    
    def remove_module(self, module_config: ModuleConfig):
        if module_config.module_name in self.active_modules:
            del self.active_modules[module_config.module_name]
        return self.active_modules
    
    def get_active_modules(self):
        return self.active_modules
    
    def save_module(self, module_config: ModuleConfig, module_data):
        module = self.active_modules[module_config.module_name]
        module.save_module(module_config, module_data)
        
    def register_module(self, module_config: ModuleConfig):
        self.module_configs.append(module_config)
        with open("data/instance_data/module_configs.json", "w", encoding="utf-8") as f:
            f.write(json.dumps(self.module_configs, indent=4))
        with open("modules/registry.json", "w", encoding="utf-8") as f:
            f.write(json.dumps(self.modules, indent=4))
        
    def list_modules(self):
        print("Active Modules:")
        for name in self.active_modules:
            print(f"- {name}")

    def cli(self):
        options = {
            "1": "Add a Module Config",
            "2": "Install Module",
            "3": "Activate Module",
            "4": "Remove Module",
            "5": "Select config",
            "6": "List Modules",
            "7": "Exit",
        }

        while True:
            print("\nModule Manager CLI")
            for key, description in options.items():
                print(f"{key}. {description}")
                
            user_input = input("Enter option: ")
            if user_input in options:
                if user_input == "1":
                    self.add_module()
                if user_input == "2":
                    self.install_module(self.module_config)
                    subprocess.run(["bash", f"{self.module_config.module_path}/install_{self.module_config.module_name}.sh"], check=True)
                if user_input == "3":
                    self.activate_module(self.module_config)
                if user_input == "4":
                    self.remove_module(self.module_config)
                if user_input == "5":
                    self.get_active_modules()
                if user_input == "6":
                    self.list_modules()
                if user_input == "7":
                    break
            else:
                print("Invalid option. Please try again.")
            
            
        
                
if __name__ == "__main__":
    manager = ModuleManager()
    manager.cli()