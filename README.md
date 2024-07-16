# Module-Miner

Module-Miner is a flexible and extensible framework for managing and running mining modules on various blockchain networks. It provides a modular architecture that allows easy integration of different mining algorithms and blockchain protocols.

## Features

- Modular design for easy integration of new mining algorithms and blockchain protocols
- Support for multiple cryptocurrencies (including Substrate-based chains, Solana, and Bitcoin)
- Secure key management with encryption
- CLI interface for easy management of modules and miners
- FastAPI-based API for remote management and monitoring
- Extensible architecture allowing for custom module development

## Components

### Core Components

- module_manager.py: Manages the loading, installation, and configuration of mining modules
- data_models.py: Defines data models used throughout the project
- base_miner.py: Provides a base class for implementing miners
- base_module.py: Provides a base class for implementing mining modules

### Utilities

- encryption.py: Handles encryption and key management functions
- parse_function.py: Parses Python code to extract function calls and create function maps

### Chain-specific Components

- commune_key_manager.py: Manages keys for the Commune blockchain

## Installation

1. Clone the repository:
   git clone https://github.com/yourusername/Module-Miner.git
   cd Module-Miner

2. Install the required dependencies:
   pip install -r requirements.txt

3. Set up your environment variables by creating a .env file in the project root:
   MINER_NAME=your_miner_name
   KEYPATH_NAME=/path/to/your/keyfile
   MINER_HOST=0.0.0.0
   EXTERNAL_ADDRESS=your_external_ip
   MINER_PORT=5757
   STAKE=275
   NETUID=0
   FUNDING_KEY=your_funding_key
   MODIFIER=15
   MODULE_NAME=your_module_name
   PRIVATE_KEY_PASSWORD=your_password

## Usage

### CLI Interface

To start the Module-Miner CLI:

python module_manager.py

This will present you with options to add module configs, install modules, select modules, list modules, remove modules, or exit.

### API

To start the API server:

python api.py

The API will be available at http://localhost:5757 (or the port specified in your .env file).

## Adding New Modules

To add a new mining module:

1. Create a new directory under modules/ with your module name
2. Implement your module following the BaseModule interface
3. Add any necessary configuration to module_configs.json
4. Use the CLI or API to install and activate your new module

## Security

Module-Miner uses strong encryption for key management. Make sure to keep your .env file and key files secure and never share them publicly.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

[Add your chosen license here]