from src.blockchain_utils.transaction_repository import (
    ApplicationTransactionRepository,
    ASATransactionRepository,
    PaymentTransactionRepository,
)
from src.services import NetworkInteraction
from algosdk import logic as algo_logic
from algosdk.future import transaction as algo_txn
from pyteal import compileTeal, Mode
from algosdk.encoding import decode_address
from src.smart_contracts import NFTMarketplaceASC1, nft_escrow


class NFTMarketplace:
    def __init__(
            self, admin_pk, admin_address, nft_id, client
    ):
        # TODO: rename admin => owner ?
        self.admin_pk = admin_pk
        self.admin_address = admin_address
        self.nft_id = nft_id

        self.client = client

        self.teal_version = 4
        self.nft_marketplace_asc1 = NFTMarketplaceASC1()

        self.app_id = None

    @property
    def escrow_address(self):
       return algo_logic.get_application_address(self.app_id)

    def app_initialization(self, nft_owner_address):
        approval_program_compiled = compileTeal(
            self.nft_marketplace_asc1.approval_program(),
            mode=Mode.Application,
            version=4,
        )

        clear_program_compiled = compileTeal(
            self.nft_marketplace_asc1.clear_program(),
            mode=Mode.Application,
            version=4
        )

        approval_program_bytes = NetworkInteraction.compile_program(
            client=self.client, source_code=approval_program_compiled
        )

        clear_program_bytes = NetworkInteraction.compile_program(
            client=self.client, source_code=clear_program_compiled
        )

        app_args = [
            decode_address(nft_owner_address),
            decode_address(self.admin_address),
        ]

        app_transaction = ApplicationTransactionRepository.create_application(
            client=self.client,
            creator_private_key=self.admin_pk,
            approval_program=approval_program_bytes,
            clear_program=clear_program_bytes,
            global_schema=self.nft_marketplace_asc1.global_schema,
            local_schema=self.nft_marketplace_asc1.local_schema,
            app_args=app_args,
            foreign_assets=[self.nft_id],
        )

        tx_id = NetworkInteraction.submit_transaction(
            self.client, transaction=app_transaction
        )

        transaction_response = self.client.pending_transaction_info(tx_id)

        self.app_id = transaction_response["application-index"]

        return tx_id

    def initialize_escrow(self):
        app_args = [
            self.nft_marketplace_asc1.AppMethods.initialize_escrow,
            decode_address(self.escrow_address),
        ]

        initialize_escrow_txn = ApplicationTransactionRepository.call_application(
            client=self.client,
            caller_private_key=self.admin_pk,
            app_id=self.app_id,
            on_complete=algo_txn.OnComplete.NoOpOC,
            app_args=app_args,
            foreign_assets=[self.nft_id],
        )

        tx_id = NetworkInteraction.submit_transaction(
            self.client, transaction=initialize_escrow_txn
        )

        return tx_id

    def fund_escrow(self):
        fund_escrow_txn = PaymentTransactionRepository.payment(
            client=self.client,
            sender_address=self.admin_address,
            receiver_address=self.escrow_address,
            amount=1000000,
            sender_private_key=self.admin_pk,
            sign_transaction=True,
        )

        tx_id = NetworkInteraction.submit_transaction(
            self.client, transaction=fund_escrow_txn
        )

        return tx_id

    def open_sell(self, sell_price: int, caller_pk):
        app_args = [self.nft_marketplace_asc1.AppMethods.open_sell, sell_price]

        app_call_txn = ApplicationTransactionRepository.call_application(
            client=self.client,
            caller_private_key=caller_pk,
            app_id=self.app_id,
            on_complete=algo_txn.OnComplete.NoOpOC,
            app_args=app_args,
            sign_transaction=True,
        )

        tx_id = NetworkInteraction.submit_transaction(self.client, transaction=app_call_txn)
        return tx_id

    def buy_nft(self, nft_owner_address, buyer_address, buyer_pk, buy_price):
        app_args = [
            self.nft_marketplace_asc1.AppMethods.buy, buyer_address
        ]
        app_call_txn = ApplicationTransactionRepository.call_application(client=self.client,
                                                                         caller_private_key=buyer_pk,
                                                                         app_id=self.app_id,
                                                                         on_complete=algo_txn.OnComplete.NoOpOC,
                                                                         app_args=app_args,
                                                                         sign_transaction=True)

        # Payment transaction: buyer -> escrow
        asa_buy_payment_txn = PaymentTransactionRepository.payment(client=self.client,
                                                                   sender_address=buyer_address,
                                                                   receiver_address=self.escrow_address,
                                                                   amount=buy_price,
                                                                   sender_private_key=buyer_pk,
                                                                   sign_transaction=True)
        tx_id = NetworkInteraction.submit_transaction(self.client, transaction=app_call_txn)
        tx_id = NetworkInteraction.submit_transaction(self.client, transaction=asa_buy_payment_txn)
        return tx_id

    def validate_buy(self, buyer_pk):
        app_args = [
            self.nft_marketplace_asc1.AppMethods.validate_buy
        ]

        app_call_txn = ApplicationTransactionRepository.call_application(client=self.client,
                                                                         caller_private_key=buyer_pk,
                                                                         app_id=self.app_id,
                                                                         on_complete=algo_txn.OnComplete.NoOpOC,
                                                                         app_args=app_args,
                                                                         sign_transaction=True)

        tx_id = NetworkInteraction.submit_transaction(self.client, transaction=app_call_txn)
        return tx_id

    def cancel_buy(self, caller_pk):
        """
        Only accessible by the owner
        """
        app_args = [self.nft_marketplace_asc1.AppMethods.cancel_buy]

        app_call_txn = ApplicationTransactionRepository.call_application(
            client=self.client,
            caller_private_key=caller_pk,
            app_id=self.app_id,
            on_complete=algo_txn.OnComplete.NoOpOC,
            app_args=app_args,
            sign_transaction=True,
        )

        tx_id = NetworkInteraction.submit_transaction(self.client, transaction=app_call_txn)
        return tx_id

    def close_sell(self, caller_pk):
        """
        Only accessible by the owner
        """
        app_args = [self.nft_marketplace_asc1.AppMethods.close]

        app_call_txn = ApplicationTransactionRepository.call_application(
            client=self.client,
            caller_private_key=caller_pk,
            app_id=self.app_id,
            on_complete=algo_txn.OnComplete.NoOpOC,
            app_args=app_args,
            sign_transaction=True,
        )

        tx_id = NetworkInteraction.submit_transaction(self.client, transaction=app_call_txn)
        return tx_id
