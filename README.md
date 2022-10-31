# Evermore: _Get ever more out of products_
Womenhack Lisbon 2022 - Project

 Team:
---
- Arielle Pompiliusa - Researcher / Video Outliner (pompiliusa@gmail.com)
- Floriane Le Floch  - Smart Contract Dev (florianelf@gmail.com)
- Mariana Constantin - Researcher / Readme (maruconstantin@gmail.com) 
- Robin Lim - Business Strategist /Deck (robinlim.fm@gmail.com) 
- Su-Zeong Froehlich - Researcher / Web Designer (szfroehlich@posteo.de)

About Evermore: 
---
Evermore is a phygital platform that allows physical goods to be sold as non-fungible tokens (NFT) by merchants and consumers on a 2nd hand market to maximize secondary sales revenue. Any NFT owner can resell their products once they decide they are not using them anymore. This is aimed to incentivise merchants to design more durable products by creating additional revenue streams from 2nd hand sales.

## How does Evermore works?
—

Powered by Blockchain and NFTs under the hood, stakeholders don’t need to onboard into the blockchain. Which means that the front end is a web2 user friendly platform.



- Merchants create/mint the NFT (Upload their collections onto the Evermore Mkt Place)
- Each NFT is going to be associated with each own smart contract to manage its life cycle in the marketplace.
- Each NFT is linked to a physical product which contains an NFC Chip or a unique and permanent code.
- NFTs contain meta data/properties such as material composition, provenance and product warranty of each physical product.
- The creator of the NFT is going to receive royalties for each sell, as long as the NFT lasts.
- The owner decides whether or not to list its product on the marketplace and for which price
- If listed, it can be bought.
- If not listed, the “buy” button will not be enabled.
- Sale is managed by the smart contract: when a user buys a product, the money is locked into the smart contract and the NFT becomes non-sellable. When the user receives the product at home, they can validate the business transaction. The NFT is finally transfered to the buyer, the seller receives the money and the creator the royalties. 
- So for each 2nd hand customer, a portion of the revenue will be transferred to the original merchant via smart contracts and royalties encoded into the NFTs, generating additional revenue streams for merchants from 2nd hand sales as well.
- When a product reaches the end of its life, then the product + the NFTs are sold to recycling companies


### Incentives to transact on-chain
- Easy listing and liquid 2nd hand market 
- Smart pricing to calculate 2nd hand price, etc. 
- Secure transactions 
- Provenance and Authentication 
- Buyer pays into an escrow 
- When buyer receives product, confirms purchase, and claims NFT, money will  be transferred to seller

## How to use this project ?

1/ Create a config.yml following this syntax:
```
accounts:
  account_1:
    address: PUBLIC_KEY_VALUE
    mnemonic: MNEMONIC_WORDS
  account_2:
    address: PUBLIC_KEY_VALUE
    mnemonic: MNEMONIC_WORDS
  account_3:
    address: PUBLIC_KEY_VALUE
    mnemonic: MNEMONIC_WORDS
  total: 3

client_credentials:
  algo_api_address: ADDRESS_VALUE
  api_secret: TOKEN_VALUE
  
pinata:
  api_key: API_KEY
  api_secret: API_SECRET"
```
- Accounts are ALGORAND wallets
- Client credentials are created by signing up on purestake plateform
- Pinata credentials are created by signing up on Pinata plateform (optional)

2/ Create a virtual environment and install the requirements
```
pip install requirements.txt
```

3/ Run the demo.py file to try out the contract.
It will upload a batch of NFTs, then run a complete selling process on the last NFT
```
python demo.py
```