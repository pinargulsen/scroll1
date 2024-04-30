from loguru import logger
from datetime import datetime

from config import OWLTO_CONTRACT, OWLTO_ABI
from utils.gas_checker import check_gas
from utils.helpers import retry
from .account import Account


class Owlto(Account):
    def __init__(self, account_id: int, private_key: str, recipient: str) -> None:
        super().__init__(account_id=account_id, private_key=private_key, chain="scroll", recipient=recipient)

        self.contract = self.get_contract(OWLTO_CONTRACT, OWLTO_ABI)

    async def get_checkin_status(self):
        return await self.contract.functions.checkInData(
            self.address,
            int(datetime.now().strftime('%Y%m%d'))
        ).call()

    @retry
    @check_gas
    async def check_in(self):
        logger.info(f"[{self.account_id}][{self.address}] OwlTo Daily CheckIn")

        checked = await self.get_checkin_status()
        if checked:
            return logger.info(f"[{self.account_id}][{self.address}] OwlTo Daily CheckIn Already Done")

        tx_data = await self.get_tx_data()

        transaction = await self.contract.functions.checkIn(
            int(datetime.now().strftime('%Y%m%d'))
        ).build_transaction(tx_data)

        signed_txn = await self.sign(transaction)

        txn_hash = await self.send_raw_transaction(signed_txn)

        await self.wait_until_tx_finished(txn_hash.hex())