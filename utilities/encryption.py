import os
import secrets
import json
import base64
from pathlib import Path
from dotenv import load_dotenv
from loguru import logger

from mnemonic import Mnemonic
from eth_hash.backends import pysha3
from scalecodec.utils.ss58 import ss58_encode
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes, padding, serialization
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from substrateinterface import Keypair as SubstrateKeypair
from solders.keypair import Keypair as SolanaKeypair
from bitcoinlib.wallets import Wallet

load_dotenv()

KEY_FOLDER = os.getenv("KEY_FOLDER")
PRIVATE_KEY = Path(f"{KEY_FOLDER}/private_key.pem")
PUBLIC_KEY = Path(f"{KEY_FOLDER}/public_key.pem")
PASSWORD = os.getenv("PRIVATE_KEY_PASSWORD").encode()
KEY_DATA = f"{KEY_FOLDER}/key_data.json"


NEMO = Mnemonic("english")


class KeyDataError(Exception):
    """Exception raised for errors retrieving key data."""


def default_backend():
    """
    A function that returns the default backend function for keccak256 hashing.
    """
    return pysha3.keccak256


def derive_rsa_keypair_with_password(
    private_path=PRIVATE_KEY, public_path=PUBLIC_KEY, password=PASSWORD
):
    """
    Generates an RSA key pair with a specified private and public path and password for encryption.

    Args:
        private_path (str): The path to save the private key. Defaults to the value of PRIVATE_KEY.
        public_path (str): The path to save the public key. Defaults to the value of PUBLIC_KEY.
        password (bytes): The password for encryption. Defaults to the value of PASSWORD.

    Returns:
        tuple: A tuple containing the public key and private key generated.
    """
    private_key = rsa.generate_private_key(
        public_exponent=65537, key_size=2048, backend=default_backend()
    )
    public_key = private_key.public_key()
    pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.BestAvailableEncryption(
            password or serialization.NoEncryption()
        ),
    )
    # encrypted_pem = ecrypt_with_password(pem, password)
    with open(private_path, "wb") as f:
        f.write(pem)
    logger.info(f"New key pair generated and saved to {private_path}")
    with open(public_path, "wb") as f:
        f.write(
            public_key.public_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PublicFormat.SubjectPublicKeyInfo,
            )
        )
    return public_key, private_key


def derive_rsa_key(password=PASSWORD, salt=os.urandom(16), length=32):
    """
    Derives an RSA key from a given password using PBKDF2HMAC with SHA256 as the hash algorithm.

    Args:
        password (bytes, optional): The password used to derive the RSA key. Defaults to the value of PASSWORD.
        salt (bytes, optional): The salt used in the key derivation process. Defaults to a randomly generated 16-byte salt.
        length (int, optional): The desired length of the derived key. Defaults to 32.

    Returns:
        bytes: The derived RSA key.

    Raises:
        None

    Notes:
        - The PBKDF2HMAC algorithm is used to derive the key from the password.
        - The SHA256 hash algorithm is used as the underlying hash function.
        - The key derivation process is performed 100,000 times.
        - The key is derived using the provided password, salt, and length.
    """
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=length,
        salt=salt,
        iterations=100000,
        backend=pysha3.keccak256,
    )
    return kdf.derive(password)


def derive_substrate_key(seed):
    """
    Creates a SubstrateKeypair object from the provided seed.

    Args:
        seed: The seed used to create the SubstrateKeypair.

    Returns:
        SubstrateKeypair: The SubstrateKeypair object created from the seed.
    """
    return SubstrateKeypair.create_from_seed(seed)


def derive_solana_key(seed):
    """
    Derives a Solana keypair from a given seed.

    Args:
        seed (bytes): The seed used to derive the Solana keypair.

    Returns:
        dict: A dictionary containing the derived Solana private key and public key.

    Raises:
        None

    Example:
        >>> seed = b'my_seed'
        >>> derive_solana_key(seed)
        {'sol_private_key': b'my_private_key', 'sol_public_key': b'my_public_key'}
    """
    sol = SolanaKeypair.from_seed(seed)
    return {"sol_private_key": sol.secret(), "sol_public_key": sol.pubkey()}


def derive_btc_key(seed):
    """
    Derives a Bitcoin key from a given seed.

    Args:
        seed (bytes): The seed used to derive the Bitcoin key.

    Returns:
        dict: A dictionary containing the derived Bitcoin private key.

    Raises:
        None

    Example:
        >>> seed = b'my_seed'
        >>> derive_btc_key(seed)
        {'btc_private_key': b'my_private_key'}
    """
    btcwallet = Wallet.create(name="test3", keys=seed, network="bitcoin")
    return {"btc_private_key": btcwallet.get_key()}


def ecrypt_with_password(data, password):
    """
    Encrypts the given data with a password using AES encryption.

    Args:
        data: The data to be encrypted.
        password: The password used to derive the encryption key.

    Returns:
        bytes: The salt + IV + encrypted data.

    Raises:
        None
    """
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
    """
    Decrypts the given encrypted data using the provided password.

    Args:
        encrypted_data (bytes): The encrypted data to be decrypted.
        password (str): The password used to derive the decryption key.

    Returns:
        bytes: The decrypted data.

    Raises:
        None

    This function takes in an encrypted data and a password as input. It first converts the encrypted data to bytes.
    Then, it extracts the salt and initialization vector (IV) from the encrypted data. The actual encrypted data is
    obtained by slicing the encrypted data starting from the 32nd byte.

    Next, the function derives a decryption key from the password and salt using the `derive_rsa_key` function.

    The decryption process involves creating a cipher object using AES algorithm with the derived key and the IV.
    A decryptor object is created from the cipher. The actual decryption is performed by updating the decryptor
    with the actual encrypted data and finalizing it. The decrypted padded data is obtained.

    To unpad the data, an unpadder object is created using the AES algorithm and the derived key's block size.
    The unpadder is then used to update the decrypted padded data and finalize it.

    Finally, the function returns the unpadded decrypted data.

    Example:
        >>> encrypted_data = b'saltivencrypteddata'
        >>> password = 'my_password'
        >>> decrypt_with_password(encrypted_data, password)
        b'decrypted_data'
    """
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
    """
    Encrypts the given data using the provided RSA key pair.

    Args:
        data (bytes): The data to be encrypted.
        password (str, optional): The password used to derive the encryption keys. Defaults to PASSWORD.
        private_path (Path, optional): The path to the private key file. Defaults to PRIVATE_KEY.
        public_path (Path, optional): The path to the public key file. Defaults to PUBLIC_KEY.
        public_encryption (bool, optional): Whether to encrypt the data with the public key. Defaults to True.
        private_encryption (bool, optional): Whether to encrypt the data with the private key. Defaults to True.

    Returns:
        tuple: A tuple containing the encrypted data, the path to the private key file, and the path to the public key file.

    Raises:
        KeyDataError: If no password is provided.

    This function takes in the data to be encrypted, along with various optional parameters. It first checks if the
    public and private key files exist. If not, it generates a new RSA key pair.

    Next, it decrypts the private key using the provided password. It then loads the public and private keys from
    the respective files.

    If no password is provided, it raises a KeyDataError.

    It then creates an empty dictionary to store the encrypted data. The data is assigned to both the "public" and
    "private" keys.

    If public encryption is enabled, it encrypts the data using the public key and stores the encrypted data in the
    "public" key of the dictionary.

    If private encryption is enabled, it decrypts the private key using the provided password. If public encryption
    is also enabled, it encrypts the encrypted data (from the "public" key) using the decrypted private key. Otherwise,
    it encrypts the original data using the decrypted private key.

    Finally, it returns a tuple containing the encrypted data, the path to the private key file, and the path to the
    public key file.

    Example:
        >>> data = b'Hello, world!'
        >>> password = 'my_password'
        >>> encrypted_data, private_path, public_path = encrypt_with_rsa_file(data, password)
        >>> print(encrypted_data)
        {'public': b'...', 'private': b'...'}
        >>> print(private_path, public_path)
        /path/to/private_key.pem /path/to/public_key.pem
    """
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
    """
    Decrypts the given data using the provided RSA key pair.

    Args:
        data (bytes): The data to be decrypted.
        password (str, optional): The password used to derive the encryption keys. Defaults to PASSWORD.
        private_path (Path, optional): The path to the private key file. Defaults to PRIVATE_KEY.
        public_path (Path, optional): The path to the public key file. Defaults to PUBLIC_KEY.
        public_encryption (bool, optional): Whether to decrypt the data with the public key. Defaults to True.
        private_encryption (bool, optional): Whether to decrypt the data with the private key. Defaults to True.

    Returns:
        dict: A dictionary containing the decrypted data. The data is assigned to both the "public" and "private" keys.

    Raises:
        KeyDataError: If no password is provided.

    This function takes in the data to be decrypted, along with various optional parameters. It first checks if the
    private key file exists. If not, it generates a new RSA key pair.

    Next, it decrypts the private key using the provided password. It then loads the public and private keys from
    the respective files.

    If no password is provided, it raises a KeyDataError.

    It then creates an empty dictionary to store the decrypted data. The data is assigned to both the "public" and
    "private" keys.

    If public decryption is enabled, it decrypts the data using the public key and stores the decrypted data in the
    "public" key of the dictionary.

    If private decryption is enabled, it decrypts the private key using the provided password. If public decryption
    is also enabled, it decrypts the encrypted data (from the "public" key) using the decrypted private key. Otherwise,
    it decrypts the original data using the decrypted private key.

    Finally, it returns a dictionary containing the decrypted data.

    Example:
        >>> data = b'Hello, world!'
        >>> password = 'my_password'
        >>> decrypted_data = decrypt_with_rsa_file(data, password)
    """
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
    """
    Generates a mnemonic phrase based on the provided strength.

    Args:
        strength (int): The strength of the mnemonic phrase in bits. Default is 256.

    Returns:
        str: The generated mnemonic phrase.
    """
    entropy = secrets.randbits(strength)
    return NEMO.to_mnemonic(entropy.to_bytes(strength // 8, "big"))


def generate_rsa_keypair_with_password(password=PASSWORD):
    """
    Generates an RSA key pair with a specified password for encryption.

    Args:
        password (bytes): The password for encryption. Defaults to the value of PASSWORD.

    Returns:
        tuple: A tuple containing the PEM-encoded private key and public key generated.
    """
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    public_key = private_key.public_key()

    pem_private = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.BestAvailableEncryption(password),
    )
    pem_public = public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    )
    save_file(pem_private, PRIVATE_KEY)
    save_file(pem_public, PUBLIC_KEY)

    return pem_private, pem_public


def extract_public_key_from_pem(pem_data):
    """
    Extracts the public key from a PEM-encoded data.

    Args:
        pem_data (bytes): The PEM-encoded data containing the public key.

    Returns:
        bytes: The extracted public key. If the key is not an RSA public key, it is returned in the raw format.
        If the key is an RSA public key, the modulus is extracted and returned as a 32-byte long byte string.

    Raises:
        ValueError: If the provided PEM data is not a valid public key.

    """
    public_key = serialization.load_pem_public_key(pem_data)
    if not isinstance(public_key, rsa.RSAPublicKey):
        # For other key types, try the raw format
        return public_key.public_bytes(
            encoding=serialization.Encoding.Raw, format=serialization.PublicFormat.Raw
        )[-32:]
    # For RSA keys, we need to extract the modulus
    numbers = public_key.public_numbers()
    return numbers.n.to_bytes(256, byteorder="big")[-32:]  # Take the last 32 bytes


def extract_private_key_from_pem(pem_data, password=PASSWORD):
    """
    Extracts the private key from a PEM-encoded data.

    Args:
        pem_data (bytes): The PEM-encoded data containing the private key.
        password (bytes): The password for decryption. Defaults to the value of PASSWORD.

    Returns:
        bytes: The extracted private key. If the key is not an RSA private key, it is returned in the raw format.
        If the key is an RSA private key, the modulus is extracted and returned as a 32-byte long byte string.
    """
    private_key = serialization.load_pem_private_key(pem_data, password=password)
    if not isinstance(private_key, rsa.RSAPrivateKey):
        # For other key types, try the raw format
        return private_key.private_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PrivateFormat.Raw,
            encryption_algorithm=serialization.BestAvailableEncryption(password),
        )
    # For RSA keys, we need to extract the modulus
    numbers = private_key.private_numbers()
    return numbers.p.to_bytes(256, byteorder="big")[-32:]


def save_file(pem, pem_path):
    """
    Saves a PEM file to the specified path. If the file already exists, prompts the user to overwrite it.

    Args:
        pem (bytes): The PEM data to be saved.
        pem_path (str): The path where the PEM file will be saved.

    Returns:
        None
    """
    if os.path.exists(pem_path):
        print(f"{pem_path} already exists")
        overwrite = input("Press enter to overwrite: ")
        if overwrite == "":
            os.remove(pem_path)
        else:
            raise ValueError(f"{pem_path} already exists")

    else:
        os.makedirs(os.path.dirname(pem_path), exist_ok=True)
    with open(pem_path, "wb") as key_file:
        key_file.write(pem)


def encode_ss58_address(public_key, prefix=42):
    """
    Encodes a public key into an ss58 address.

    Args:
        public_key (bytes or str): The public key to encode. If a string is provided, it is assumed to be a hexadecimal representation of the key.
        prefix (int, optional): The ss58 address prefix. Defaults to 42.

    Returns:
        str: The ss58 address encoded from the public key.

    Raises:
        ValueError: If the public key is not 32 bytes.
    """
    if isinstance(public_key, str):
        public_key = bytes.fromhex(public_key)

    if len(public_key) != 32:
        raise ValueError("Public key must be 32 bytes")

    return ss58_encode(public_key, prefix)


def construct_key_data(
    rsa_private_key,
    rsa_public_key,
    ss58key,
    mnemonic,
    private_key,
    public_key,
    ss58_prefix=42,
    key_data_path=KEY_DATA,
):
    """
    Constructs key data with RSA private and public keys, ss58key, mnemonic, private and public keys.
    Optionally accepts ss58 prefix and key data path.
    Returns the constructed key data.
    """

    key_data = {
        "rsa_private_key": base64.b64encode(rsa_private_key).decode("utf-8"),
        "rsa_public_key": base64.b64encode(rsa_public_key).decode("utf-8"),
        "private_key": private_key,
        "public_key": public_key,
        "ss58key": ss58key,
        "mnemonic": mnemonic,
        "ss58_prefix": ss58_prefix,
        "path": key_data_path,
    }
    key_path = Path(key_data_path)
    key = {"data": json.dumps(key_data)}
    key_path.write_text(json.dumps(key), encoding="utf-8")
    return key_data


def encode_password(password):
    """
    Encodes a password into bytes by decoding it using 'utf-8'.

    Args:
        password (str): The password to be encoded.

    Returns:
        str: The password encoded as bytes.
    """
    password_bytes = password.decode("utf-8")
    return password_bytes


if __name__ == "__main__":
    derive_rsa_keypair_with_password(PRIVATE_KEY, PUBLIC_KEY, PASSWORD)
