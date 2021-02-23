#!/usr/bin/python3

"""Coincalculators API module"""

import requests

from ethpay import EthPay


class CoinCalculators():
    BASE_API = 'https://www.coincalculators.io/api'
    CC_API = BASE_API + '?name=:crypto:&hashrate=:hrate:'

    __crypto = None

    eth_pay = None

    def __init__(self, crypto):
        """Init of CoinCalculators class."""
        self.__crypto = crypto
        self.eth_pay = EthPay()

    def __api_request(self, api_url):
        """Make CoinCalculators API call"""
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

    def update(self, hrate):
        """Update CoinCalculators informations."""
        cust_url = self.CC_API.replace(':crypto:', self.__crypto)
        cust_url = cust_url.replace(':hrate:', str(hrate * 1000000))
        cc_json = self.__api_request(cust_url)
        if cc_json is not None:
            self.eth_pay.eth_hour = round(cc_json['rewardsInHour'], 5)
            self.eth_pay.eth_day = round(cc_json['rewardsInDay'], 5)
            self.eth_pay.eth_week = round(cc_json['rewardsInWeek'], 5)
            self.eth_pay.eth_month = round(cc_json['rewardsInMonth'], 5)
