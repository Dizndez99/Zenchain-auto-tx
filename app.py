from web3 import Web3
import time
import os
from dotenv import load_dotenv
from datetime import datetime
from colorama import Fore, Style, init
import secrets

# Inisialisasi Colorama
init(autoreset=True)

# Simbol dan warna
CHECK_MARK = Fore.GREEN + "✔️" + Style.RESET_ALL
CROSS_MARK = Fore.RED + "❌" + Style.RESET_ALL
BALANCE_SYMBOL = Fore.CYAN + "💰" + Style.RESET_ALL
ZEN_SYMBOL = Fore.YELLOW + "ZCX" + Style.RESET_ALL
SENDER_ADDRESS_SYMBOL = Fore.CYAN + "📤 Alamat Pengirim:" + Style.RESET_ALL
RECEIVER_ADDRESS_SYMBOL = Fore.MAGENTA + "📥 Alamat Penerima:" + Style.RESET_ALL
AMOUNT_SYMBOL = Fore.LIGHTYELLOW_EX + "💵 Jumlah Kiriman:" + Style.RESET_ALL

# Load variabel dari file .env
load_dotenv()

# Endpoint RPC dan Chain ID Zenchain Testnet
RPC_URL = "https://zenchain-testnet.api.onfinality.io/public"  # RPC URL Zenchain Testnet
CHAIN_ID = 8408  # Zenchain Testnet Chain ID
web3 = Web3(Web3.HTTPProvider(RPC_URL))

# Periksa koneksi ke node
if web3.is_connected():
    print(Fore.GREEN + f"Terkoneksi dengan jaringan Zenchain Testnet {CHECK_MARK}")
else:
    print(Fore.RED + f"Gagal terhubung ke jaringan Zenchain Testnet {CROSS_MARK}")
    raise Exception("Gagal terhubung ke jaringan Zenchain Testnet")

# Load akun dari file .env
accounts = []
index = 1
while True:
    sender_address = os.getenv(f'SENDER_ADDRESS_{index}')
    private_key = os.getenv(f'PRIVATE_KEY_{index}')
    if not sender_address or not private_key:
        break
    accounts.append((web3.to_checksum_address(sender_address), private_key))
    index += 1

if not accounts:
    raise Exception("Harap isi SENDER_ADDRESS dan PRIVATE_KEY di file .env")

# Fungsi untuk mendapatkan saldo
def get_balance(address):
    return web3.from_wei(web3.eth.get_balance(address), 'ether')

# Fungsi untuk mendapatkan nonce
def get_nonce(address):
    return web3.eth.get_transaction_count(address)

# Fungsi untuk membuat alamat acak
def generate_random_address():
    private_key = secrets.token_hex(32)  # Private key acak
    account = web3.eth.account.from_key(private_key)
    return account.address

# Fungsi untuk mengirim transaksi 0.1 ZCX
def send_transaction(sender_address, private_key, receiver_address, amount=0.1):
    nonce = get_nonce(sender_address)
    gas_price = web3.eth.gas_price

    # Validasi saldo
    sender_balance = get_balance(sender_address)
    if sender_balance < amount:
        print(Fore.RED + f"Saldo tidak cukup. Saldo: {sender_balance:.18f} ZCX, Jumlah: {amount:.18f} ZCX {CROSS_MARK}")
        return

    print(Fore.BLUE + f"{BALANCE_SYMBOL} Saldo Pengirim: {sender_balance:.18f} ZCX")
    print(f"{SENDER_ADDRESS_SYMBOL} {sender_address}")
    print(f"{RECEIVER_ADDRESS_SYMBOL} {receiver_address}")
    print(f"{AMOUNT_SYMBOL} {amount:.18f} ZCX")

    # Membuat transaksi
    tx = {
        'nonce': nonce,
        'to': receiver_address,
        'value': web3.to_wei(amount, 'ether'),  # Kirim 0.1 ZCX
        'gas': 21000,
        'gasPrice': gas_price,
        'chainId': CHAIN_ID  # Zenchain Testnet Chain ID
    }

    try:
        # Menandatangani transaksi
        signed_tx = web3.eth.account.sign_transaction(tx, private_key)
        # Kirim transaksi
        tx_hash = web3.eth.send_raw_transaction(signed_tx.raw_transaction)
        print(Fore.GREEN + f"{datetime.now()} - Transaksi berhasil! Hash: {web3.to_hex(tx_hash)} {CHECK_MARK}")
    except Exception as e:
        print(Fore.RED + f"Gagal mengirim transaksi: {e} {CROSS_MARK}")

# Loop utama
while True:
    for sender_address, private_key in accounts:
        print("\n" + Fore.YELLOW + "-" * 50)
        # Generate alamat acak untuk setiap transaksi
        random_receiver_address = generate_random_address()
        send_transaction(sender_address, private_key, random_receiver_address, amount=0.1)  # Kirim 0.1 ZCX
        print(Fore.YELLOW + "-" * 50)
        time.sleep(15)  # Jeda 15 detik antara transaksi