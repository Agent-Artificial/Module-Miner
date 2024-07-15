import os
import json
from pydantic import BaseModel, Field
from typing import Dict, Any, List
from base.base_module import BaseModule
from base.base_miner import MinerConfig, ModuleConfig, BaseMiner
from importlib import import_module
from dotenv import load_dotenv

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


class ModuleManager:
    modules: Dict[str, Any]
    active_modules: Dict[str, Any]
    module_configs: Dict[str, Any]
    
    def __init__(self):
        self.modules = {}
        self.active_modules = {}
        self.module_configs = self.get_configs()
        
    def get_configs(self):
        configs = []
        if os.path.exists("data/instance_data/module_configs.json"):
            with open("data/instance_data/module_configs.json", "r", encoding="utf-8") as f:
                configs = json.loads(f.read())
        else:
            if not os.path.exists("data/instance_data"):
                os.makedirs("data/instance_data")
            with open("data/instance_data/module_configs.json", "w", encoding="utf-8") as f:
                f.write(json.dumps(configs, indent=4))
        return configs

    def get_module(self):
        for config in self.module_configs:
            module_name = config.module_name
            for dir in os.listdir("modules"):
                if config in dir:
                    module = import_module(f"{dir}.{module_name}")
                    self.modules[module_name] = module
        with open("modules/registry.json", "w", encoding="utf-8") as f:
            f.write(self.modules)
        return self.modules
    
    def add_module_config(self):
        module_config = ModuleConfig(
            module_name=input("Enter module_name: "),
            module_path=input("Enter module_path: "),
            module_endpoint=input("Enter module_endpoint: "),
            module_url=input("Enter module_url: ")
        )
        self.module_configs[module_config.module_name] = module_config.model_dump()
        with open("data/instance_data/module_configs.json", "w", encoding="utf-8") as f:
            f.write(json.dumps(self.module_configs, indent=4))
        module = self.install_module(module_config)
        self.modules = module
        return self.module_configs
    
    def install_module(self, module_config: ModuleConfig):
        module = BaseModule(module_config)
        if module.check_for_existing_module():
            overwrite = input("Module already exists. Overwrite? [y/n]: ")
            if overwrite == ("y" or "yes" or "Y" or "YES" or ""):
                module.install_module(module_config)
            else:
                return
        else:
            module.install_module(module_config)
            with open("data/instance_data/module_configs.json", "w", encoding="utf-8") as f:
                f.write(json.dumps(self.module_configs, indent=4))
            module = self.modules[module_config.module_name]
            module.save_module(module_config, module.get_module())
            with open("modules/registry.json", "w", encoding="utf-8") as f:
                f.write(json.dumps(self.modules, indent=4))
        self.modules[module_config.module_name] = module
        self.active_modules[module_config.module_name] = module
        module.setup_module()
        return module
    
    def activate_module(self, module_config: ModuleConfig):
        if module_config.module_name in self.modules:
            self.active_modules[module_config.module_name] = self.modules[module_config.module_name]
        else:
            self.install_module(module_config)
            
        self.active_modules[module_config.module_name].setup_module(miner_config)
        return self.active_modules
    
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
            "1": ("Add a Module Config", self.add_module_config),
            "2": ("Install Module", self.install_module),
            "3": ("Activate Module", self.activate_module),
            "4": ("Remove Module", self.remove_module),
            "5": ("Select config", self.get_active_modules),
            "6": ("List Modules", self.list_modules),
            "7": ("Exit", exit)
        }

        while True:
            print("\nModule Manager CLI")
            for key, (description, _) in options.items():
                print(f"{key}. {description}")

            choice = input("Enter your choice: ")
            for key, (_, action) in options.items():
                if choice == "1":
                    action()
                elif choice == "2":
                    module_name = input("Enter module_name: ")
                    if module_name not in self.module_configs:
                        options["1"][1]()
                        module_name = self.module_configs[module_name]
                    module_config = self.module_configs[module_name]
                    action()
                elif choice == "3":
                    module_name = input("Enter module_name: ")
                    module_config = self.module_configs[module_name] or options["1"][1]()
                    action(module_config)
                elif choice == "4":
                    module_name = input("Enter module_name: ")
                    action(module_name)
                elif choice == "5":
                    print(list(action().keys(), "\n"))
                elif choice == "6":
                    action(list(action().keys(), "\n"))
                elif choice == "7":
                    exit()
                if choice == key:
                    break
            else:
                print("Invalid choice. Please try again.")
        
                
if __name__ == "__main__":
    manager = ModuleManager()
    manager.cli()