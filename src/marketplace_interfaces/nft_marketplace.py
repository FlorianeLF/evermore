from abc import ABC, abstractmethod


class NFTMarketplaceInterface(ABC):

    @abstractmethod
    def initialize_escrow(self, escrow_address):
        pass

    @abstractmethod
    def open_sell(self, sell_price):
        pass

    @abstractmethod
    def buy(self, buyer_address):
        pass

    @abstractmethod
    def close_sell(self):
        pass

    @abstractmethod
    def validate_buy(self):
        pass

    @abstractmethod
    def cancel_buy(self):
        pass