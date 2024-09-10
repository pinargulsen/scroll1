from loguru import logger
from datetime import datetime
import aiohttp
import random

from config import PUMP_CONTRACT, PUMP_ABI
from utils.gas_checker import check_gas
from utils.helpers import retry
from .account import Account


class Pump(Account):
    def __init__(self, account_id: int, private_key: str, recipient: str) -> None:
        super().__init__(account_id=account_id, private_key=private_key, chain="scroll", recipient=recipient)

        self.contract = self.get_contract(PUMP_CONTRACT, PUMP_ABI)

    async def get_claim_data(self):
        headers = {
            'accept': 'application/json, text/plain, */*',
            'accept-language': 'ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7',
            'origin': 'https://scrollpump.xyz',
            'priority': 'u=1, i',
            'referer': 'https://scrollpump.xyz/',
            'sec-ch-ua': '"Chromium";v="128", "Not;A=Brand";v="24", "Google Chrome";v="128"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"macOS"',
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'same-site',
            'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36',
        }

        params = {
            'address': self.address,
        }

        async with aiohttp.ClientSession() as session:
            async with session.get(
                url="https://api.scrollpump.xyz/api/Airdrop/GetSign",
                headers=headers,
                params=params,
            ) as r:
                data = await r.json()
                if data.get("success"):
                    return data.get("data")
                else:
                    return False

    @retry
    async def claim(self):
        logger.info(f"[{self.account_id}][{self.address}] Pump AirDrop Claiming")

        claim_data = await self.get_claim_data()
        if not claim_data:
            return logger.info(f"[{self.account_id}][{self.address}] No claim data")

        logger.debug(f"[{self.account_id}][{self.address}] Claim {self.w3.from_wei(int(claim_data.get('amount')), 'ether')} $PUMP")

        tx_data = await self.get_tx_data()

        transaction = await self.contract.functions.claim(
            int(claim_data.get("amount")),
            claim_data.get("sign"),
            self.w3.to_checksum_address(random.choice(["0x1C7FF320aE4327784B464eeD07714581643B36A7", "0x009FcB59420DF23c07D82FC9A410628948E5F4F9"]))
        ).build_transaction(tx_data)

        signed_txn = await self.sign(transaction)

        txn_hash = await self.send_raw_transaction(signed_txn)

        await self.wait_until_tx_finished(txn_hash.hex())