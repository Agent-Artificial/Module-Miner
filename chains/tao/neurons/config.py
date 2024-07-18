from bittensor.config import config


def get_config():
    return {
        "add_args": {
            "netuid": {"type": int, "help": "Subnet netuid", "default": 1},
            "neuron.device": {"type": str, "help": "Device to run on.", "default": "is_cuda_available()"},
            "neuron.epoch_length": {
                "type": int,
                "help": "The default epoch length (how often we set weights, measured in 12 second blocks).",
                "default": 100,
            },
            "mock": {
                "action": "store_true",
                "help": "Mock neuron and all network components.",
                "default": False,
            },
            "neuron.events_retention_size": {
                "type": str,
                "help": "Events retention size.",
                "default": 2 * 1024 * 1024 * 1024,  # 2 GB
            },
            "neuron.dont_save_events": {
                "action": "store_true",
                "help": "If set, we dont save events to a log file.",
                "default": False,
            },
            "wandb.off": {
                "action": "store_true",
                "help": "Turn off wandb.",
                "default": False,
            },
            "wandb.offline": {
                "action": "store_true",
                "help": "Runs wandb in offline mode.",
                "default": False,
            },
            "wandb.notes": {
                "type": str,
                "help": "Notes to add to the wandb run.",
                "default": "",
            },
        },
        "add_miner_args": {
            "neuron.name": {
                "type": str,
                "help": "Trials for this neuron go in neuron.root / (wallet_cold - wallet_hot) / neuron.name. ",
                "default": "miner",
            },
            "blacklist.force_validator_permit": {
                "action": "store_true",
                "help": "If set, we will force incoming requests to have a permit.",
                "default": False,
            },
            "blacklist.allow_non_registered": {
                "action": "store_true",
                "help": "If set, miners will accept queries from non registered entities. (Dangerous!)",
                "default": False,
            },
            "wandb.project_name": {
                "type": str,
                "default": "template-miners",
                "help": "Wandb project to log to.",
            },
            "wandb.entity": {
                "type": str,
                "default": "opentensor-dev",
                "help": "Wandb entity to log to.",
            },
        },
        "add_validator_args": {
            "neuron.name": {
                "type": str,
                "help": "Trials for this neuron go in neuron.root / (wallet_cold - wallet_hot) / neuron.name. ",
                "default": "validator",
            },
            "neuron.timeout": {
                "type": float,
                "help": "The timeout for each forward call in seconds.",
                "default": 10,
            },
            "neuron.num_concurrent_forwards": {
                "type": int,
                "help": "The number of concurrent forwards running at any time.",
                "default": 1,
            },
            "neuron.sample_size": {
                "type": int,
                "help": "The number of miners to query in a single step.",
                "default": 50,
            },
            "neuron.disable_set_weights": {
                "action": "store_true",
                "help": "Disables setting weights.",
                "default": False,
            },
            "neuron.moving_average_alpha": {
                "type": float,
                "help": "Moving average alpha parameter, how much to add of the new observation.",
                "default": 0.1,
            },
            "neuron.axon_off": {
                "action": "store_true",
                "help": "Set this flag to not attempt to serve an Axon.",
                "default": False,
            },
            "neuron.vpermit_tao_limit": {
                "type": int,
                "help": "The maximum number of TAO allowed to query a validator with a vpermit.",
                "default": 4096,
            },
            "wandb.project_name": {
                "type": str,
                "help": "The name of the project where you are sending the new run.",
                "default": "template-validators",
            },
            "wandb.entity": {
                "type": str,
                "help": "The name of the project where you are sending the new run.",
                "default": "opentensor-dev",
            },
        },
    }