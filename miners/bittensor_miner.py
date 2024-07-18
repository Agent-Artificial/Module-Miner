import os
from importlib import import_module
from chains.tao.neurons.miner import TAOMiner, default_config
from data_models import ModuleConfig, app
from dotenv import load_dotenv

load_dotenv()


module_config = ModuleConfig(
    module_name="translation",
    module_path="modules/translation",
    module_endpoint="/modules/translation",
    module_url="https://registrar-cellium.ngrok.app"
)
bittensor_miner = TAOMiner(module_config, config=default_config)
module = import_module(f"{module_config.module_path.replace('/', '.')}.{module_config.module_name}")

bittensor_miner.set_module(module_config)

print("You can register your miner. Registration cost is 1 TAO.")
register = input("Register miner? [y/N]: ")
if register.lower() in ["yes", "y"]:
    bittensor_miner.register_miner()

bittensor_miner.serve_miner(app)