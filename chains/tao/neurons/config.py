import contextlib
from pydantic import BaseModel, Field, TypeAdapter
from typing import Optional, Optional, Dict, List, Union
import argparse
import os
import subprocess
import bittensor as bt


def is_cuda_available():
    with contextlib.suppress(Exception):
        output = subprocess.check_output(["nvidia-smi", "-L"], stderr=subprocess.STDOUT)
        if "NVIDIA" in output.decode("utf-8"):
            return "cuda"
    with contextlib.suppress(Exception):
        output = subprocess.check_output(["nvcc", "--version"]).decode("utf-8")
        if "release" in output:
            return "cuda"
    return "cpu"


class NeuronConfig(BaseModel):
    name: str = "test_miner_hot"
    device: str = Field(default_factory=is_cuda_available)
    epoch_length: int = 100
    events_retention_size: int = 2 * 1024 * 1024 * 1024  # 2 GB
    dont_save_events: bool = False
    full_path: Optional[str] = None


class WandbConfig(BaseModel):
    off: bool = True
    offline: bool = True
    notes: str = ""
    project_name: str = "example-project"
    entity: str = "eden_subnet"


class BlacklistConfig(BaseModel):
    force_validator_permit: bool = True
    allow_non_registered: bool = False


class MinerConfig(BaseModel):
    neuron: NeuronConfig = Field(default_factory=lambda: NeuronConfig(name="test_miner_hot"))
    wandb: WandbConfig = Field(
        default_factory=lambda: WandbConfig(project_name="eden_subnet-miners")
    )
    blacklist: BlacklistConfig = Field(default_factory=BlacklistConfig)


class ValidatorConfig(BaseModel):
    neuron: NeuronConfig = Field(default_factory=lambda: NeuronConfig(name="validator_test"))
    wandb: WandbConfig = Field(
        default_factory=lambda: WandbConfig(project_name="eden_subnet-validators")
    )
    timeout: float = 10.0
    num_concurrent_forwards: int = 1
    sample_size: int = 50
    disable_set_weights: bool = False
    moving_average_alpha: float = 0.1
    axon_off: bool = False
    vpermit_tao_limit: int = 4096


class Config(BaseModel):
    netuid: int = 1
    mock: bool = False
    neuron: NeuronConfig = Field(default_factory=NeuronConfig)
    wandb: WandbConfig = Field(default_factory=WandbConfig)
    miner: Optional[MinerConfig] = None
    validator: Optional[ValidatorConfig] = None


def check_config(config: Config):
    bt.logging.check_config(config)

    full_path = os.path.expanduser(
        f"{config.logging.logging_dir}/{config.wallet.name}/{config.wallet.hotkey}/netuid{config.netuid}/{config.neuron.name}"
    )
    print("full path:", full_path)
    config.neuron.full_path = os.path.expanduser(full_path)
    if not os.path.exists(config.neuron.full_path):
        os.makedirs(config.neuron.full_path, exist_ok=True)

    if not config.neuron.dont_save_events:
        # Add custom event logger for the events.
        events_logger = bt.setup_events_logger(
            config.neuron.full_path, config.neuron.events_retention_size
        )
        bt.logging.register_primary_logger(events_logger.name)


def generate_default_config(is_miner: bool = True) -> Config:
    base_config = Config()
    if is_miner:
        base_config.miner = MinerConfig()
    else:
        base_config.validator = ValidatorConfig()

    return base_config


def config_to_dict(config: Union[BaseModel, dict]) -> dict:
    if isinstance(config, dict):
        return {k: config_to_dict(v) for k, v in config.items()}
    if isinstance(config, list):
        return [config_to_dict(i) for i in config]
    if isinstance(config, BaseModel):
        return config_to_dict(config.model_dump(exclude_unset=True))


def get_config(is_miner: bool = True, use_cli: bool = False):
    # Generate default configuration
    default_config = generate_default_config(is_miner)

    config = parse_configs(default_config) if use_cli else default_config
    check_config(config)
    return config


# TODO Rename this here and in `get_config`
def parse_configs(default_config):

    # Convert default config to a flat dictionary for argparse
    default_dict = config_to_dict(default_config)
    flat_defaults = {f"{k1}.{k2}": v2 
                     for k1, v1 in default_dict.items() 
                     for k2, v2 in v1.items() if isinstance(v1, dict)}

    # Create parser with default values
    parser = argparse.ArgumentParser()
    for key, value in flat_defaults.items():
        parser.add_argument(f"--{key}", default=value, type=type(value))

    # Parse arguments
    args = parser.parse_args()

    # Convert args back to nested dictionary
    config_dict = {}
    for key, value in vars(args).items():
        parts = key.split('.')
        d = config_dict
        for part in parts[:-1]:
            if part not in d:
                d[part] = {}
            d = d[part]
        d[parts[-1]] = value

    return Config.model_validate(config_dict)