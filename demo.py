from natsort import natsorted
import requests
import glob

from src.blockchain_utils.credentials import (get_algo_client,
                                              get_account_credentials,
                                              get_pinata_credentials)
from src.services.nft_service import NFTService
from src.services.nft_marketplace import NFTMarketplace

client = get_algo_client()
admin_pk, admin_addr, _ = get_account_credentials(1)
buyer_pk, buyer_addr, _ = get_account_credentials(2)


def create_nft_services(manufacturer_name, unit_name, id, nft_url=None):
    nft_service = NFTService(nft_creator_address=admin_addr,
                             nft_creator_pk=admin_pk,
                             client=client,
                             unit_name=unit_name,
                             asset_name=manufacturer_name + '-' + str(id),
                             nft_url=nft_url)

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


def get_nft_cid(n, image_path, api_key, api_secret):
    img = natsorted(glob.glob(image_path))
    files = [img]
    headers = {'pinata_api_key': api_key,'pinata_secret_api_key': api_secret}

    ipfs_url = "https://api.pinata.cloud/pinning/pinFileToIPFS"

    response: requests.Response = requests.post(url=ipfs_url, files=files, headers=headers)
    meta = response.json()
    print(meta)  # to confirm Pinata Storage limit has not been reached
    return meta['IpfsHash']


def main():
    product_ids = range(1,5)
    manufacturer_name = "ManufacturerA@collection1"
    unit_name = "MANA@C1"
    image_path = "./images/bike.jpeg"
    pinata_key, pinata_secret = get_pinata_credentials()
    sell_price = 100000
    nft_url = "QmYf24YppoPFyWe1aDNXjNMTqewAoJ4S4esucYNbR9dmoz"
    for id in product_ids:
        print("\n\nCREATING NFT %s" % id)
        nft_smart_contract_service, nft_service = create_nft_services(
            manufacturer_name, unit_name, id, nft_url=nft_url
        )

    # On the last contract, let's list our NFT and run a transaction
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