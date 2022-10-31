from pyteal import *
import algosdk

from src.marketplace_interfaces import NFTMarketplaceInterface


@Subroutine(TealType.none)
def inner_payment_txn(amount: TealType.uint64, receiver: TealType.bytes):
    """casual payment transaction"""
    return Seq([
        InnerTxnBuilder.Begin(),
        InnerTxnBuilder.SetFields({
            TxnField.type_enum: TxnType.Payment,
            TxnField.sender: Global.current_application_address(),
            TxnField.amount: amount,
            TxnField.receiver: receiver
        }),
        InnerTxnBuilder.Submit()
    ])


@Subroutine(TealType.none)
def executeAssetTransfer(asset_id: TealType.uint64, asset_amount: TealType.uint64, asset_sender: TealType.bytes,
                         asset_receiver: TealType.bytes) -> Expr:
    return Seq([
        InnerTxnBuilder.Begin(),
        InnerTxnBuilder.SetFields({
            TxnField.type_enum: TxnType.AssetTransfer,
            TxnField.xfer_asset: asset_id,
            TxnField.asset_sender: asset_sender,
            TxnField.asset_amount: asset_amount,
            TxnField.asset_receiver: asset_receiver
        }),
        InnerTxnBuilder.Submit()
    ])


class NFTMarketplaceASC1(NFTMarketplaceInterface):
    """
    Smart Contract to control the full life cycle of an NFT on our Marketplace
    """
    class Variables:
        escrow_address = Bytes("ESCROW_ADDRESS")
        asa_id = Bytes("ASA_ID")
        asa_price = Bytes("ASA_PRICE")
        asa_owner = Bytes("ASA_OWNER")
        asa_buyer = Bytes("ASA_BUYER")
        app_state = Bytes("APP_STATE")
        app_admin = Bytes("APP_ADMIN")
        asa_creator = Bytes("ASA_CREATOR")
        creator_royalties = Bytes("CREATOR_ROYALTIES")

    class AppMethods:
        initialize_escrow = "initializeEscrow"
        open_sell = "openSell"
        buy = "buy"
        close_sell = "closeSell"
        validate_buy = "validateBuy"
        cancel_buy = "cancelBuy"
        execute_transaction = "executeTransaction"

    class AppState:
        not_initialized = Int(0)
        active = Int(1)
        selling_open = Int(2)
        buying_in_progress = Int(3)
        buy_validated = Int(4)

    def application_start(self):
        actions = Cond(
            [Txn.application_id() == Int(0), self.app_initialization()],

            [Txn.application_args[0] == Bytes(self.AppMethods.initialize_escrow),
             self.initialize_escrow(escrow_address=Txn.application_args[1])],

            [Txn.application_args[0] == Bytes(self.AppMethods.open_sell),
             self.open_sell(sell_price=Txn.application_args[1])],

            [Txn.application_args[0] == Bytes(self.AppMethods.buy),
             self.buy(buyer_address=Txn.application_args[1])],

            [Txn.application_args[0] == Bytes(self.AppMethods.validate_buy),
             self.validate_buy()],

            [Txn.application_args[0] == Bytes(self.AppMethods.cancel_buy),
             self.cancel_buy()],

            [Txn.application_args[0] == Bytes(self.AppMethods.close_sell), self.close_sell()]
        )

        return actions

    def app_initialization(self):
        """
        CreateAppTxn with 2 arguments: asa_owner, app_admin.
        The foreign_assets array should have 1 asa_id which will be the id of the NFT of interest.
        This function is called only once, the asa_id can't be changed
        :return:
        """
        return Seq([
            Assert(Txn.application_args.length() == Int(2)),
            App.globalPut(self.Variables.app_state, self.AppState.not_initialized),
            App.globalPut(self.Variables.asa_id, Txn.assets[0]),
            App.globalPut(self.Variables.asa_owner, Txn.application_args[0]),
            App.globalPut(self.Variables.app_admin, Txn.application_args[1]),
            # default empty value
            App.globalPut(self.Variables.asa_buyer, Global.zero_address()),
            App.globalPut(self.Variables.creator_royalties, Int(10)),
            # The first owner of the NFT will stay the creator for ever
            App.globalPut(self.Variables.asa_creator, Txn.application_args[0]),
            Return(Int(1))
        ])

    def initialize_escrow(self, escrow_address):
        """
        Application call from the app_admin.
        :return:
        """
        curr_escrow_address = App.globalGetEx(Int(0), self.Variables.escrow_address)

        asset_escrow = AssetParam.clawback(Txn.assets[0])
        manager_address = AssetParam.manager(Txn.assets[0])
        freeze_address = AssetParam.freeze(Txn.assets[0])
        reserve_address = AssetParam.reserve(Txn.assets[0])
        default_frozen = AssetParam.defaultFrozen(Txn.assets[0])

        return Seq([
            curr_escrow_address,
            Assert(curr_escrow_address.hasValue() == Int(0)),

            Assert(App.globalGet(self.Variables.app_admin) == Txn.sender()),
            Assert(Global.group_size() == Int(1)),

            asset_escrow,
            manager_address,
            freeze_address,
            reserve_address,
            default_frozen,
            Assert(Txn.assets[0] == App.globalGet(self.Variables.asa_id)),
            Assert(asset_escrow.value() == Txn.application_args[1]),
            Assert(default_frozen.value()),
            Assert(manager_address.value() == Global.zero_address()),
            Assert(freeze_address.value() == Global.zero_address()),
            Assert(reserve_address.value() == Global.zero_address()),

            App.globalPut(self.Variables.escrow_address, escrow_address),
            App.globalPut(self.Variables.app_state, self.AppState.active),
            Return(Int(1))
        ])

    def open_sell(self, sell_price):
        """
        Function for the owner to list its product/NFT in the marketplace
        """
        valid_number_of_transactions = Global.group_size() == Int(1)
        app_is_active = Or(App.globalGet(self.Variables.app_state) == self.AppState.active,
                           App.globalGet(self.Variables.app_state) == self.AppState.selling_open)

        valid_seller = Txn.sender() == App.globalGet(self.Variables.asa_owner)
        valid_number_of_arguments = Txn.application_args.length() == Int(2)

        can_sell = And(valid_number_of_transactions,
                       app_is_active,
                       valid_seller,
                       valid_number_of_arguments)

        update_state = Seq([
            App.globalPut(self.Variables.asa_price, Btoi(sell_price)),
            App.globalPut(self.Variables.app_state, self.AppState.selling_open),
            Return(Int(1))
        ])

        return If(can_sell).Then(update_state).Else(Return(Int(0)))

    def buy(self, buyer_address):
        """
        Function to buy the NFT
        """
        app_sell_is_open = App.globalGet(self.Variables.app_state) == self.AppState.selling_open
        no_current_buy = App.globalGet(self.Variables.asa_buyer) == Global.zero_address()
        can_buy = And( app_sell_is_open,
                       no_current_buy)

        update_state = Seq([
            App.globalPut(self.Variables.asa_buyer, buyer_address),
            App.globalPut(self.Variables.app_state, self.AppState.buying_in_progress),
            Return(Int(1))
        ])

        return If(can_buy).Then(update_state).Else(Return(Int(0)))

    def validate_buy(self):
        """
        Function for the buyer has received the product at home and can now agree to transfer the money
        to the original owner and become the NFT owner
        :return:
        """
        buying_in_progress = App.globalGet(self.Variables.app_state) == self.AppState.buying_in_progress
        can_validate_buying = buying_in_progress
        # The transaction is validated
        royalties = Div(Btoi(self.Variables.creator_royalties) * Btoi(self.Variables.asa_price), Int(100))
        seller_money =  Btoi(self.Variables.asa_price) - royalties

        # 1. send the money from smart contract to the original NFT owner
        If(can_validate_buying).Then(
            inner_payment_txn(
                seller_money,
                self.Variables.asa_owner)
        ).Else(Return(Int(0)))


        # 2. send the NFT from the smart contract into the buyer wallet
        If(can_validate_buying).Then(executeAssetTransfer(
           self.Variables.asa_id,
           Int(1),
           self.Variables.escrow_address,
           self.Variables.asa_buyer)
        ).Else(Return(Int(0)))

        # 3. Send out the royalties to the creator
        If(can_validate_buying).Then(
            inner_payment_txn(
                royalties,
                self.Variables.asa_creator)
        ).Else(Return(Int(0)))

        # The NFT is sold, let's reset the global state to the "active" state with the new owner
        # Up to the new owner to list the NFT again or not
        update_state = Seq([
            App.globalPut(self.Variables.app_state, self.AppState.active),
            App.globalPut(self.Variables.asa_owner, self.Variables.asa_buyer),
            App.globalPut(self.Variables.asa_buyer, Global.zero_address()),
            Return(Int(1))
        ])
        # TODO: check inner transaction to send the NFT from here + insert the royalties here (calculate %)
        return If(can_validate_buying).Then(update_state).Else(Return(Int(0)))

    def cancel_buy(self):
        """
        Function for the owner to cancel a buying process, and get its NFT back.
        The buyer gets its money back as well
        """
        valid_number_of_transactions = Global.group_size() == Int(3)
        valid_caller = Txn.sender() == App.globalGet(self.Variables.asa_owner)
        buying_in_progress = App.globalGet(self.Variables.app_state) == self.AppState.buying_in_progress

        can_cancel_buying = And(valid_number_of_transactions,
                                valid_caller,
                                buying_in_progress)

        # State goes back to selling open
        update_state = Seq([
            App.globalPut(self.Variables.app_state, self.AppState.selling_open),
            App.globalPut(self.Variables.asa_buyer, Global.zero_address()),
            Return(Int(1))
        ])

        return If(can_cancel_buying).Then(update_state).Else(Return(Int(0)))

    def close_sell(self):
        """
        The owner don't want to have its product listing on the marketplace anymore
        """
        valid_number_of_transactions = Global.group_size() == Int(1)
        valid_caller = Txn.sender() == App.globalGet(self.Variables.asa_owner)
        app_is_initialized = App.globalGet(self.Variables.app_state) != self.AppState.not_initialized

        can_stop_selling = And(valid_number_of_transactions,
                               valid_caller,
                               app_is_initialized)

        update_state = Seq([
            App.globalPut(self.Variables.app_state, self.AppState.active),
            Return(Int(1))
        ])

        return If(can_stop_selling).Then(update_state).Else(Return(Int(0)))

    def approval_program(self):
        return self.application_start()

    def clear_program(self):
        return Return(Int(1))

    @property
    def global_schema(self):
        return algosdk.future.transaction.StateSchema(num_uints=5,
                                                      num_byte_slices=5)

    @property
    def local_schema(self):
        return algosdk.future.transaction.StateSchema(num_uints=0,
                                                      num_byte_slices=0)
