import os
import time
import secrets
from datetime import datetime
from dotenv import load_dotenv
from web3 import Web3
import rich
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn
from rich.live import Live
from rich.text import Text

# Inisialisasi
load_dotenv()
console = Console()

# Konfigurasi
class Config:
    RPC_URL = os.getenv('RPC_URL', 'https://zenchain-testnet.api.onfinality.io/public')
    CHAIN_ID = 8408
    TRANSACTION_INTERVAL = 15
    AMOUNT_TO_SEND = 0.001
    MAX_TRANSACTION_HISTORY = 10

class ZenchainTransactionMonitor:
    def __init__(self):
        # Koneksi Web3
        self.web3 = Web3(Web3.HTTPProvider(Config.RPC_URL))
        
        # Validasi koneksi
        if not self.web3.is_connected():
            console.print("[bold red]Gagal terhubung ke jaringan Zenchain Testnet[/bold red]")
            raise Exception("Koneksi Gagal")
        
        # Inisialisasi variabel
        self.transaction_history = []
        self.load_accounts()

    def load_accounts(self):
        self.accounts = []
        index = 1
        while True:
            sender_address = os.getenv(f'SENDER_ADDRESS_{index}')
            private_key = os.getenv(f'PRIVATE_KEY_{index}')
            if not sender_address or not private_key:
                break
            self.accounts.append((
                self.web3.to_checksum_address(sender_address), 
                private_key
            ))
            index += 1

        if not self.accounts:
            console.print("[bold red]Harap isi SENDER_ADDRESS dan PRIVATE_KEY di file .env[/bold red]")
            raise Exception("Tidak ada akun")

    def get_balance(self, address):
        return self.web3.from_wei(self.web3.eth.get_balance(address), 'ether')

    def generate_random_address(self):
        """Membuat alamat Ethereum acak"""
        private_key = secrets.token_hex(32)
        account = self.web3.eth.account.from_key(private_key)
        return account.address

    def send_transaction(self, sender_address, private_key, amount=Config.AMOUNT_TO_SEND):
        try:
            # Generate alamat penerima acak
            receiver_address = self.generate_random_address()
            
            # Cek saldo
            sender_balance = self.get_balance(sender_address)
            if sender_balance < amount:
                console.print(f"[bold red]Saldo tidak cukup: {sender_balance:.4f} ZCX[/bold red]")
                return None

            # Persiapan transaksi
            nonce = self.web3.eth.get_transaction_count(sender_address)
            gas_price = self.web3.eth.gas_price

            tx = {
                'nonce': nonce,
                'to': receiver_address,
                'value': self.web3.to_wei(amount, 'ether'),
                'gas': 21000,
                'gasPrice': gas_price,
                'chainId': Config.CHAIN_ID
            }

            # Tanda tangani dan kirim transaksi
            signed_tx = self.web3.eth.account.sign_transaction(tx, private_key)
            tx_hash = self.web3.eth.send_raw_transaction(signed_tx.raw_transaction)
            
            # Simpan riwayat transaksi
            tx_detail = {
                'timestamp': datetime.now(),
                'sender': sender_address,
                'receiver': receiver_address,
                'amount': amount,
                'tx_hash': self.web3.to_hex(tx_hash)
            }
            self.transaction_history.append(tx_detail)
            
            # Batasi riwayat
            if len(self.transaction_history) > Config.MAX_TRANSACTION_HISTORY:
                self.transaction_history.pop(0)
            
            return tx_detail

        except Exception as e:
            console.print(f"[bold red]Gagal mengirim transaksi: {e}[/bold red]")
            return None

    def display_transaction_history(self):
        """Tampilkan riwayat transaksi dalam tabel yang menarik"""
        table = Table(title="Riwayat Transaksi Zenchain")
        
        # Definisi kolom
        table.add_column("Waktu", style="cyan")
        table.add_column("Pengirim", style="magenta")
        table.add_column("Penerima", style="green")
        table.add_column("Jumlah", style="yellow")
        table.add_column("Tx Hash", style="blue")
        
        # Tambahkan baris
        for tx in reversed(self.transaction_history):
            table.add_row(
                str(tx['timestamp'].strftime("%Y-%m-%d %H:%M:%S")),
                tx['sender'][:10] + "...",
                tx['receiver'][:10] + "...",
                f"{tx['amount']:.4f} ZCX",
                tx['tx_hash'][:20] + "..."
            )
        
        console.print(table)

    def run_continuous_transactions(self):
        """Jalankan transaksi berkelanjutan dengan tampilan interaktif"""
        with Live(console=console, refresh_per_second=1) as live:
            while True:
                for sender_address, private_key in self.accounts:
                    # Panel informasi akun
                    account_panel = Panel(
                        f"[bold green]Akun: {sender_address[:10]}...[/bold green]\n"
                        f"[yellow]Saldo: {self.get_balance(sender_address):.4f} ZCX[/yellow]",
                        title="Informasi Akun",
                        border_style="blue"
                    )
                    live.update(account_panel)

                    # Kirim transaksi
                    tx_result = self.send_transaction(sender_address, private_key)
                    
                    if tx_result:
                        # Tampilkan detail transaksi
                        tx_panel = Panel(
                            f"[bold green]✅ Transaksi Berhasil[/bold green]\n"
                            f"[cyan]Pengirim:[/cyan] {tx_result['sender'][:10]}...\n"
                            f"[green]Penerima:[/green] {tx_result['receiver'][:10]}...\n"
                            f"[yellow]Jumlah:[/yellow] {tx_result['amount']:.4f} ZCX\n"
                            f"[blue]Tx Hash:[/blue] {tx_result['tx_hash'][:20]}...",
                            title="Detail Transaksi",
                            border_style="green"
                        )
                        live.update(tx_panel)

                    # Tampilkan riwayat transaksi
                    self.display_transaction_history()
                    
                    # Jeda antar transaksi
                    time.sleep(Config.TRANSACTION_INTERVAL)

def main():
    console.print("[bold blue]🚀 Zenchain Testnet Random Transaction Sender[/bold blue]")
    
    try:
        tx_monitor = ZenchainTransactionMonitor()
        tx_monitor.run_continuous_transactions()
    except Exception as e:
        console.print(f"[bold red]Error: {e}[/bold red]")

if __name__ == "__main__":
    main()
