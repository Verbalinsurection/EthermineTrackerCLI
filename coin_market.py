#!/usr/bin/python3

"""Coin market API module"""

import requests
from datetime import datetime


class Coin():
    BASE_API = 'https://api.coingecko.com/api/v3'
    API_COIN = BASE_API + '/coins/markets?vs_currency=:fiat:&ids=:crypto:'

    __fiat = None
    __crypto = None

    price = 0.0
    pc_24h = 0.0
    ath = 0.0
    last_update = ''
    last_update_txt = ''

    def __init__(self, fiat, crypto):
        """Init of Coin class."""
        self.__fiat = fiat
        self.__crypto = crypto

    def __api_request(self, api_url):
        """Make Ethermine API call"""
        try:
            response = requests.get(api_url, timeout=5)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as errh:
            print(errh)
            return None
        except requests.exceptions.ConnectionError as errc:
            print(errc)
            return None
        except requests.exceptions.Timeout as errt:
            print(errt)
            return None
        except requests.exceptions.RequestException as err:
            print(err)
            return None

    def update(self):
        """Update coin market informations."""
        cust_url = self.API_COIN.replace(':fiat:', self.__fiat)
        cust_url = cust_url.replace(':crypto:', self.__crypto)
        coin_json = self.__api_request(cust_url)
        if coin_json is not None:
            self.price = round(coin_json[0]['current_price'], 2)
            self.pc_24h = round(coin_json[0]['price_change_24h'], 2)
            self.ath = round(coin_json[0]['ath'], 2)
            self.last_update = datetime.strptime(
                                    coin_json[0]['last_updated'],
                                    "%Y-%m-%dT%H:%M:%S.%f%z").astimezone()
            self.last_update_txt = self.last_update.strftime('%Y-%m-%d %H:%M')
