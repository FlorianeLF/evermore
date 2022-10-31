from src.blockchain_utils.credentials import get_algo_client, get_account_credentials
from src.services.nft_service import NFTService
from src.services.nft_marketplace import NFTMarketplace

client = get_algo_client()
admin_pk, admin_addr, _ = get_account_credentials(1)
buyer_pk, buyer_addr, _ = get_account_credentials(2)


def create_nft_services(id):
    nft_service = NFTService(nft_creator_address=admin_addr,
                             nft_creator_pk=admin_pk,
                             client=client,
                             unit_name="MAN2@C1",
                             asset_name="Manufacturer2@collection1-" + id,
                             nft_url="bafybeih6cahp6rwzlgy2tn5sdjo33hixvem6gn5yfbtn2okfdikncnjaua")

    nft_id = nft_service.create_nft()
    print("NFT CREATED WITH ID %s in account %s" % (nft_id, admin_addr))

    nft_marketplace_service = NFTMarketplace(admin_pk=admin_pk,
                                             admin_address=admin_addr,
                                             client=client,
                                             nft_id=nft_service.nft_id)

    app_id = nft_marketplace_service.app_initialization(nft_owner_address=admin_addr)
    print("APP ID", app_id)

    nft_service.change_nft_credentials_txn(escrow_address=nft_marketplace_service.escrow_address)
    nft_marketplace_service.initialize_escrow()
    nft_marketplace_service.fund_escrow()
    return nft_marketplace_service, nft_service


def main():
    print("\n\nCREATING NFT 1")
    sell_price = 100000
    nft_smart_contract_service, nft_service = create_nft_services("1")
    nft_smart_contract_service.open_sell(sell_price=sell_price, caller_pk=admin_pk)
    nft_service.opt_in(buyer_pk)

    trx_id = nft_smart_contract_service.buy_nft(nft_owner_address=admin_addr,
                                             buyer_address=buyer_addr,
                                             buyer_pk=buyer_pk,
                                             buy_price=sell_price)
    print("nft bought by %s, transaction id %s" % (buyer_addr, trx_id))
    trx_id = nft_smart_contract_service.validate_buy(
        buyer_pk=buyer_pk
    )
    print("nft validated by %s, transaction id %s" % (buyer_addr, trx_id))



if __name__ == '__main__':
    main()