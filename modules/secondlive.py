from loguru import logger
from datetime import datetime

from config import SECONDLIVE_CONTRACT, SECONDLIVE_ABI
from utils.gas_checker import check_gas
from utils.helpers import retry
from .account import Account


class SecondLive(Account):
    def __init__(self, account_id: int, private_key: str, recipient: str) -> None:
        super().__init__(account_id=account_id, private_key=private_key, chain="scroll", recipient=recipient)

        self.contract = self.get_contract(SECONDLIVE_CONTRACT, SECONDLIVE_ABI)

    async def check_sign_in(self):
        return await self.contract.functions._signIn(
            self.address,
            int(datetime.utcnow().strftime("%Y%m%d"))
        ).call()

    @retry
    @check_gas
    async def sign_in(self):
        """
        Daily Sign In
        https://secondlive.world/bounty/general
        """

        logger.info(f"[{self.account_id}][{self.address}] SecondLive Sign In")

        signed = await self.check_sign_in()
        if signed:
            return logger.info(f"[{self.account_id}][{self.address}] SecondLive already signed today")

        tx_data = await self.get_tx_data()

        transaction = await self.contract.functions.signIn(int(datetime.utcnow().strftime("%Y%m%d"))).build_transaction(tx_data)

        signed_txn = await self.sign(transaction)

        txn_hash = await self.send_raw_transaction(signed_txn)

        await self.wait_until_tx_finished(txn_hash.hex())
