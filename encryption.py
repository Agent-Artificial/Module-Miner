import os
import secrets
import json
import base64
from pathlib import Path
from dotenv import load_dotenv 
from loguru import logger

from Crypto.Hash import keccak
from mnemonic import Mnemonic
from eth_account import Account
from eth_hash.backends import pysha3
from scalecodec.utils.ss58 import ss58_encode
from scalecodec.types import GenericAccountId
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes, padding, serialization
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from substrateinterface import Keypair as SubstrateKeypair
from solders.keypair import Keypair as SolanaKeypair
from bitcoinlib.wallets import Wallet
from base64 import urlsafe_b64encode, urlsafe_b64decode
load_dotenv()

KEY_FOLDER = os.getenv('KEY_FOLDER')
PRIVATE_KEY = Path(f"{KEY_FOLDER}/private_key.pem")
PUBLIC_KEY = Path(f"{KEY_FOLDER}/public_key.pem")
PASSWORD = os.getenv("PRIVATE_KEY_PASSWORD").encode()
KEY_DATA = f"{KEY_FOLDER}/key_data.json"


NEMO = Mnemonic("english")


class KeyDataError(Exception):
    """Exception raised for errors retrieving key data."""
     
    
def default_backend():
    return pysha3.keccak256


def derive_rsa_keypair_with_password(
    private_path=PRIVATE_KEY, 
    public_path=PUBLIC_KEY, 
    password=PASSWORD
):
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
        backend=default_backend()
    )
    public_key = private_key.public_key()
    pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.BestAvailableEncryption(password or serialization.NoEncryption())
    )
    #encrypted_pem = ecrypt_with_password(pem, password)
    with open(private_path, 'wb') as f:
        f.write(pem)
    logger.info(f"New key pair generated and saved to {private_path}")
    with open(public_path, 'wb') as f:
        f.write(public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        ))
    return public_key, private_key


def derive_rsa_key(password=PASSWORD, salt=os.urandom(16), length=32):
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=length,
        salt=salt,
        iterations=100000,
        backend=pysha3.keccak256,
    )
    return kdf.derive(password)


def derive_substrate_key(seed):
    return SubstrateKeypair.create_from_seed(seed)


def derive_solana_key(seed):
    sol = SolanaKeypair.from_seed(seed)
    return {"sol_private_key": sol.secret(), "sol_public_key": sol.pubkey()}


def derive_btc_key(seed):
    btcwallet = Wallet.create(name="test3", keys=seed, network="bitcoin")
    return {"btc_private_key": btcwallet.get_key()}


def ecrypt_with_password(data, password):
    salt = os.urandom(16)
    # Derive a key from the password
    key = derive_rsa_key(password, salt)

    # Generate a random Initialization Vector (IV)
    iv = os.urandom(16)

    # Pad the data
    padder = padding.PKCS7(algorithms.AES(key).block_size).padder()
    padded_data = padder.update(data) + padder.finalize()

    # Encrypt the data
    cipher = Cipher(algorithms.AES(key), modes.CFB(iv), backend=default_backend())
    encryptor = cipher.encryptor()
    encrypted_data = encryptor.update(padded_data) + encryptor.finalize()

    # Return the salt + iv + encrypted_data
    return salt + iv + encrypted_data


def decrypt_with_password(encrypted_data, password):
    encrypted_data = str(encrypted_data).encode()
    salt = encrypted_data[:16]
    iv = encrypted_data[16:32]
    actual_encrypted_data = encrypted_data[32:]

    # Derive the key from the password and salt
    key = derive_rsa_key(password, salt)

    # Decrypt the data
    cipher = Cipher(algorithms.AES(key), modes.CFB(iv), backend=default_backend())
    decryptor = cipher.decryptor()
    decrypted_padded_data = (
        decryptor.update(actual_encrypted_data) + decryptor.finalize()
    )

    # Unpad the data
    unpadder = padding.PKCS7(algorithms.AES(key).block_size).unpadder()
    return unpadder.update(decrypted_padded_data) + unpadder.finalize()

def encrypt_with_rsa_file(
    data,
    password=PASSWORD,
    private_path=PRIVATE_KEY,
    public_path=PUBLIC_KEY,
    public_encryption=True,
    private_encryption=True,
):
    if not public_path.exists() and not private_path.exists():
        derive_rsa_keypair_with_password()
    decrypted_private_pem = decrypt_with_password(private_path.read_bytes(), password)
    public_key = serialization.load_pem_public_key(public_path.read_bytes())
    private_key = serialization.load_pem_private_key(decrypted_private_pem, password)

    if password is None:
        raise KeyDataError("No password provided")

    decrypted_private_key = serialization.load_pem_private_key(
        decrypt_with_password(private_key, password), password=None
    )

    encrypted_data = {}
    encrypted_data["public"] = data
    encrypted_data["private"] = data
    if public_encryption:
        public_encrypt_data = public_key.encrypt(
            encrypted_data["public"],
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None,
            ),
        )
        encrypted_data["public"] = public_encrypt_data
    if private_encryption:
        if public_encryption:
            encrypted_data["private"] = decrypted_private_key.encrypt(
                encrypted_data["public"],
                padding.OAEP(
                    mgf=padding.MGF1(algorithm=hashes.SHA256()),
                    algorithm=hashes.SHA256(),
                    label=None,
                ),
            )
        else:
            encrypted_data["private"] = decrypted_private_key.encrypt(
                data,
                padding.OAEP(
                    mgf=padding.MGF1(algorithm=hashes.SHA256()),
                    algorithm=hashes.SHA256(),
                    label=None,
                ),
            )

    return encrypted_data, private_path, public_path



def decrypt_with_rsa_file(
    data,
    password=PASSWORD,
    private_path=PRIVATE_KEY,
    public_path=PUBLIC_KEY,
    public_encryption=True,
    private_encryption=True,
    ):
    if not private_path.exists():
        derive_rsa_keypair_with_password(password)

    private_key_pem = decrypt_with_password(private_path.read_bytes(), password)

    decrypted_data = {}
    decrypted_data["private"] = data
    decrypted_data["public"] = data
    if public_encryption:
        public_key = serialization.load_pem_public_key(public_path.read_bytes())
        decrypted_data["public"] = public_key.decrypt(
            decrypted_data["public"],
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None,
            ),
        )

    if private_encryption:
        private_key = serialization.load_pem_private_key(
            data=private_key_pem,
            password=PASSWORD.encode("utf-8"),
            )
        if public_encryption:
            decrypted_data["private"] = private_key.decrypt(
                decrypted_data["public"],
                padding.OAEP(
                    mgf=padding.MGF1(algorithm=hashes.SHA256()),
                    algorithm=hashes.SHA256(),
                    label=None,
                ),
            )
        else:
            decrypted_data["private"] = private_key.decrypt(
                decrypted_data["private"],
                padding.OAEP(
                    mgf=padding.MGF1(algorithm=hashes.SHA256()),
                    algorithm=hashes.SHA256(),
                    label=None,
                ),
            )

    return decrypted_data


def generate_mnemonic(strength=256):
    entropy = secrets.randbits(strength)
    return NEMO.to_mnemonic(entropy.to_bytes(strength // 8, 'big'))


def generate_rsa_keypair_with_password(password=PASSWORD):
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048
    )
    public_key = private_key.public_key()
    
    pem_private = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.BestAvailableEncryption(password)
        )
    pem_public = public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    )
    save_file(pem_private, PRIVATE_KEY)
    save_file(pem_public, PUBLIC_KEY)
    
    return pem_private, pem_public

def extract_public_key_from_pem(pem_data):
    public_key = serialization.load_pem_public_key(pem_data)
    if not isinstance(public_key, rsa.RSAPublicKey):
        # For other key types, try the raw format
        return public_key.public_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PublicFormat.Raw
        )[-32:]
    # For RSA keys, we need to extract the modulus
    numbers = public_key.public_numbers()
    return numbers.n.to_bytes(256, byteorder='big')[-32:]  # Take the last 32 bytes
        
        
def extract_private_key_from_pem(pem_data, password=PASSWORD):
    private_key = serialization.load_pem_private_key(pem_data, password=password)
    if not isinstance(private_key, rsa.RSAPrivateKey):
        # For other key types, try the raw format
        return private_key.private_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PrivateFormat.Raw,
            encryption_algorithm=serialization.BestAvailableEncryption(password)
        )
    # For RSA keys, we need to extract the modulus
    numbers = private_key.private_numbers()
    return numbers.p.to_bytes(256, byteorder='big')[-32:]


def save_file(pem, pem_path):
    if os.path.exists(pem_path):
        print(f"{pem_path} already exists")
        overwrite = input("Press enter to overwrite: ")
        if overwrite == "":
            os.remove(pem_path)
        else:
            raise ValueError(f"{pem_path} already exists")
        
    else:
        os.makedirs(os.path.dirname(pem_path), exist_ok=True)
    with open(pem_path, 'wb') as key_file:
        key_file.write(pem)
        

def encode_ss58_address(public_key, prefix=42):
    if isinstance(public_key, str):
        public_key = bytes.fromhex(public_key)
    
    if len(public_key) != 32:
        raise ValueError("Public key must be 32 bytes")
    
    return ss58_encode(public_key, prefix)


def construct_key_data(rsa_private_key, rsa_public_key, ss58key, mnemonic, private_key, public_key, ss58_prefix=42, key_data_path=KEY_DATA):
    
    key_data = {
        "rsa_private_key": base64.b64encode(rsa_private_key).decode('utf-8'),
        "rsa_public_key": base64.b64encode(rsa_public_key).decode('utf-8'),
        "private_key": private_key,
        "public_key": public_key,
        "ss58key": ss58key,
        "mnemonic": mnemonic,
        "ss58_prefix": ss58_prefix,
        "path": key_data_path
    }
    key_path = Path(key_data_path)
    key = {"data": json.dumps(key_data)}
    key_path.write_text(json.dumps(key), encoding="utf-8")
    return key_data
    

def encode_password(password):
    password_bytes = password.decode('utf-8')
    return password_bytes


if __name__ == "__main__":
    derive_rsa_keypair_with_password(PRIVATE_KEY, PUBLIC_KEY, PASSWORD)