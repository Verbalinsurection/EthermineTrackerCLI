#!/usr/bin/python3

"""Ethermine API module"""

from datetime import datetime, timedelta

import requests


class Ethermine():
    ETHM_API_BASE = 'https://api.ethermine.org'
    ETHM_API_POOLSTATS = ETHM_API_BASE + '/poolStats'
    ETHM_API_MINERDASH = ETHM_API_BASE + '/miner/:miner/dashboard'
    ETHM_API_MINERPAYOUT = ETHM_API_BASE + '/miner/:miner/payouts'
    ETHM_API_WORKER = ETHM_API_BASE + '/miner/:miner/worker/:worker/history'

    __wallet = None

    pool_state = 'N/A'
    stat_time = ''
    stat_time_txt = ''
    reported_hrate = 0
    current_hrate = 0
    valid_shares = 0
    invalid_shares = 0
    stale_shares = 0
    active_workers = 0
    last_histo = None
    max_index = 0
    unpaid_balance = 0
    min_payout = 0
    next_payout = None
    next_payout_txt = ''
    eth_hour = 0.0
    eth_day = 0.0
    eth_week = 0.0
    eth_month = 0.0
    gain_progress = 0.0

    def __init__(self, eth_wallet):
        """Init of Ethermine class."""
        self.__wallet = eth_wallet
        self.workers = []
        self.payouts = []
        self.stats_histo = []
        self.avg_hrate_1 = [0.0] * 3  # actual, 30m, 60m
        self.avg_hrate_6 = [0.0] * 3  # actual, 30m, 60m
        self.avg_hrate_24 = [0.0] * 3  # actual, 30m, 60m

    def update(self):
        """Update Ethermine informations."""
        self.__update_pool()
        self.__update_miner_dash()
        self.__update_miner_payouts()

    def __hrate_mh(self, hashrate):
        return round(hashrate / 1000000, 2)

    def api_request(self, api_url):
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

    def __update_pool(self):
        """Update Ethermine pool informations."""
        pool_json = self.api_request(self.ETHM_API_POOLSTATS)
        if pool_json is None:
            self.pool_state = 'Unavailable'
        else:
            self.pool_state = pool_json['status']

    def __update_miner_dash(self):
        """Update Ethermine miner dashboard."""
        cust_url = self.ETHM_API_MINERDASH.replace(':miner', self.__wallet)
        dash_json = self.api_request(cust_url)
        if dash_json is not None:
            try:
                data_json = dash_json['data']
                self.workers.clear()
                for json_worker in data_json['workers']:
                    worker = Worker(self.__wallet, json_worker)
                    self.workers.append(worker)
                cstat_json = data_json['currentStatistics']
                self.stat_time = datetime.fromtimestamp(
                    cstat_json['time']).astimezone()
                self.stat_time_txt = self.stat_time.strftime('%Y-%m-%d %H:%M')
                self.reported_hrate = self.__hrate_mh(
                    cstat_json['reportedHashrate'])
                self.current_hrate = self.__hrate_mh(
                    cstat_json['currentHashrate'])
                self.valid_shares = cstat_json['validShares']
                self.invalid_shares = cstat_json['invalidShares']
                self.stale_shares = cstat_json['staleShares']
                self.active_workers = cstat_json['activeWorkers']
                self.unpaid_balance = round(cstat_json['unpaid'] / 10e17, 5)
                self.min_payout = round(
                    data_json['settings']['minPayout'] / 10e17, 5)
                self.stats_histo.clear()
                for json_histo in data_json['statistics']:
                    stat_histo = EthermineH(json_histo)
                    self.stats_histo.append(stat_histo)
                self.last_histo = self.stats_histo[len(self.stats_histo) - 1 - 3]
                self.max_index = len(self.stats_histo) - 1
                self.calc_avg()
            except KeyError as e:
                print(e)

    def calc_avg(self):
        entry_num = len(self.stats_histo)
        max_index = self.max_index

        # calc avg from -24h to now
        all_hrate = 0
        for stat_histo in self.stats_histo:
            all_hrate += stat_histo.current_hrate
        self.avg_hrate_24[0] = round(all_hrate / entry_num, 0)

        # calc avg from -1h to now
        all_hrate = 0
        for index in range(6):
            all_hrate += self.stats_histo[max_index - index].current_hrate
        self.avg_hrate_1[0] = round(all_hrate / 6, 0)

        # calc avg from -6h to now
        all_hrate = 0
        for index in range(36):
            all_hrate += self.stats_histo[max_index - index].current_hrate
        self.avg_hrate_6[0] = round(all_hrate / 36, 0)

        # calc avg from -24h to -30m
        all_hrate = 0
        for index in range(entry_num - 3):
            all_hrate += self.stats_histo[index].current_hrate
        self.avg_hrate_24[1] = round(all_hrate / (entry_num - 3), 0)

        # calc avg from -1h30 to -30m
        all_hrate = 0
        for index in range(6):
            all_hrate += self.stats_histo[max_index - 3 - index].current_hrate
        self.avg_hrate_1[1] = round(all_hrate / 6, 0)

        # calc avg from -6h30 to -30m
        all_hrate = 0
        for index in range(36):
            all_hrate += self.stats_histo[max_index - 3 - index].current_hrate
        self.avg_hrate_6[1] = round(all_hrate / 36, 0)

        # calc avg from -24h to -60m
        all_hrate = 0
        for index in range(entry_num - 6):
            all_hrate += self.stats_histo[index].current_hrate
        self.avg_hrate_24[2] = round(all_hrate / (entry_num - 6), 0)

        # calc avg from -2h to -1h
        all_hrate = 0
        for index in range(6):
            all_hrate += self.stats_histo[max_index - 6 - index].current_hrate
        self.avg_hrate_1[2] = round(all_hrate / 6, 0)

        # calc avg from -7h to -1h
        all_hrate = 0
        for index in range(36):
            all_hrate += self.stats_histo[max_index - 6 - index].current_hrate
        self.avg_hrate_6[2] = round(all_hrate / 36, 0)

    def __update_miner_payouts(self):
        cust_url = self.ETHM_API_MINERPAYOUT.replace(':miner', self.__wallet)
        payouts_json = self.api_request(cust_url)
        if payouts_json is not None:
            self.payouts.clear()
            for json_payout in payouts_json['data']:
                payout = Payout(json_payout)
                self.payouts.append(payout)
        time_delta = datetime.now().astimezone() - self.payouts[0].paid_on
        time_delta_m = time_delta.days * 1440 + (time_delta.seconds / 60)
        gain_min = self.unpaid_balance / (time_delta_m)
        self.eth_hour = round(gain_min * 60, 5)
        self.eth_day = round(gain_min * 60 * 24, 5)
        self.eth_week = round(gain_min * 60 * 24 * 7, 5)
        self.eth_month = round(gain_min * 60 * 24 * 30, 5)
        self.gain_progress = self.unpaid_balance / self.min_payout

    def update_next_payout(self, actual_gain_hour):
        to_gain = self.min_payout - self.unpaid_balance
        minutes_to_tresh = to_gain / (actual_gain_hour / 60)
        self.next_payout = \
            datetime.now().astimezone() + \
            timedelta(minutes=minutes_to_tresh)
        self.next_payout_txt = self.next_payout.strftime('%Y-%m-%d %H:%M')


class EthermineH():
    stat_time = ''
    stat_time_txt = ''
    reported_hrate = 0
    current_hrate = 0
    valid_shares = 0
    invalid_shares = 0
    stale_shares = 0

    def __init__(self, json_data):
        self.stat_time = datetime.fromtimestamp(
            json_data['time']).astimezone()
        self.stat_time_txt = self.stat_time.strftime('%Y-%m-%d %H:%M')
        self.reported_hrate = self.__hrate_mh(
            json_data['reportedHashrate'])
        self.current_hrate = self.__hrate_mh(
            json_data['currentHashrate'])
        self.valid_shares = json_data['validShares']
        self.invalid_shares = json_data['invalidShares']
        self.stale_shares = json_data['staleShares']

    def __hrate_mh(self, hashrate):
        return round(hashrate / 1000000, 2)


class Worker(Ethermine):
    name = ''

    def __init__(self, wallet, json_data):
        self.stats_histo = []
        self.avg_hrate_1 = [0.0] * 3  # actual, 30m, 60m
        self.avg_hrate_6 = [0.0] * 3  # actual, 30m, 60m
        self.avg_hrate_24 = [0.0] * 3  # actual, 30m, 60m
        self.__wallet = wallet
        self.name = json_data['worker']
        self.last_seen = json_data['lastSeen']
        self.reported_hrate = json_data['reportedHashrate']
        self.current_hrate = json_data['currentHashrate']
        self.valid_shares = json_data['validShares']
        self.invalid_shares = json_data['invalidShares']
        self.stale_shares = json_data['staleShares']
        self.__process_histo()

    def __process_histo(self):
        cust_url = Ethermine.ETHM_API_WORKER.replace(':miner', self.__wallet)
        cust_url = cust_url.replace(':worker', self.name)
        dash_json = self.api_request(cust_url)
        if dash_json is not None:
            try:
                data_json = dash_json['data']
                self.stats_histo.clear()
                for json_histo in data_json:
                    stat_histo = EthermineH(json_histo)
                    self.stats_histo.append(stat_histo)
                self.last_histo = self.stats_histo[len(self.stats_histo) - 1 - 3]
                self.max_index = len(self.stats_histo) - 1
                self.calc_avg()
            except KeyError as e:
                print(e)


class Payout():
    paid_on = None
    paid_on_txt = None
    amount = None

    def __init__(self, json_data):
        self.paid_on = datetime.fromtimestamp(
            json_data['paidOn']).astimezone()
        self.paid_on_txt = self.paid_on.strftime('%Y-%m-%d %H:%M')
        self.amount = json_data['amount']
