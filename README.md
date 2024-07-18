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

### Usage

The CLI is the easiest way to install and launch a single miner.
`python -m module_manager`

Select 2. Install module

Once complete select 6 serve miner.

### API

You can manually start the API server:

python api.py

The API will be available at http://localhost:5757 (or the port specified in your .env file).

## Security

Security considerations should be made for your keys. We have provided a .env.example to help keep your secrets secure but always make sure to keep the private keys and mnemonics of your keys secret and safe. We will be implementing an encryption method for that file in the future.
Another consideration is installing arbitrary code from a third party api which creates an attack vector. To help address this we are going to be adding and public key that will correspond with a private key that only the registrar has with the repo. During the installation process the public key will be used to decode files from the registrar to ensure that they are coming from authentic source. Additionally the module code will be available for direct download from the github repo in a viewable form. You can select the module by selecting the corresponding branch in the repo.

## BTCLI Commands

### Setup Owner Coldkey
`btcli wallet new_coldkey --wallet.name owner`

### Setup Miner Cold Wallet
`btcli wallet new_coldkey --wallet.name miner`

### Setup Miner Hotkey

`btcli wallet new_hotkey --wallet.name miner --wallet.hotkey default`

### Setup Validator Cold Wallet
`btcli wallet new_coldkey --wallet.name validator`

### Setup Validator Hot Key
`btcli wallet new_hotkey --wallet.name validator --wallet.hotkey default`

### Mint Tokens
`btcli wallet faucet --wallet.name owner --subtensor.chain_endpoint ws://127.0.0.1:9946`

### Mint Tokens for Validator 
`btcli wallet faucet --wallet.name validator --subtensor.chain_endpoint ws://127.0.0.1:9946`

### Create Subnet
`btcli subnet create --wallet.name owner --subtensor.chain_endpoint ws://127.0.0.1:9946`

### Register Keys
`btcli subnet register --wallet.name miner --wallet.hotkey default --subtensor.chain_endpoint ws://127.0.0.1:9946`
`btcli subnet register --wallet.name validator --wallet.hotkey default --subtensor.chain_endpoint ws://127.0.0.1:9946`

### Add stake
`btcli stake add --wallet.name validator --wallet.hotkey default --subtensor.chain_endpoint ws://127.0.0.1:9946`

### Validate Key Registration
`btcli subnet list --subtensor.chain_endpoint ws://127.0.0.1:9946`

### Check Registered Details
`btcli wallet overview --wallet.name validator --subtensor.chain_endpoint ws://127.0.0.1:9946`
`btcli wallet overview --wallet.name miner --subtensor.chain_endpoint ws://127.0.0.1:9946`


## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

MIT
