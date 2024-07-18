from importlib import import_module
from chains.tao.neurons.miner import TAOMiner, default_config
from data_models import ModuleConfig, app


bittensor_miner = TAOMiner(config=default_config)

module_config = ModuleConfig(
    module_name="translation",
    module_path="modules/translation",
    module_endpoint="/modules/translation",
    module_url="https://registrar-cellium.ngrok.app"
)

module = import_module(f"{module_config.module_path}.{module_config.module_name}")

bittensor_miner.set_module(module)

bittensor_miner.set_process(module)

bittensor_miner.serve_module(app)