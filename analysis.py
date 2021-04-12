"""
This script serves as a way to analyze data received from the API Query (iexcloud.io). Here are some ideas we want to flush out:

To Do:

    - implement backtest
    - implement and learn Advanced Stats
        - P/E
        - put/call
        - debt/equity
        - revenue, etc

    - implement Alert System (email)
    - implement Alert Triggers
        - e.g. price drops >10% of buy price --> GET OUT 
    - implement and learn Advanced Fundamentals
    - compare Earnings/PE/EBITA
    - IPO calendar
    - dashboard to display all this information

GOALS
------

Ultimately create a bot that given $1000, can turn a profit. This is not easy.

So lets start with smaller goals.

1) Given a stock, compare its performance with its peers.

"""
import numpy as np
import pandas as pd
import os
import logging
import sys
import argparse
import pdb

# local module
from iex_api import IEXApi


class Analysis():
    """
    This Object will be used to retrieve data from the API and perform Analysis based on the data received
    """

    def __init__(self, api: IEXApi = None) -> None:
        if api is None:
            api = IEXApi(token=api_token, base_url=base_url, logger=logger)
        self.api_obj = api

    def momentum_analysis(self, stats_df: pd.DataFrame) -> pd.DataFrame:
        """
        Compares the change percent over various date ranges w/ other stocks listed in stats_df

        Args:
            stats_df (pd.DataFrame): DataFrame containing the statistics for each stock

        Returns:
            DataFrame: Momentum DataFrame w/ percent changes, respective percentiles, and an averaged percentile.
        """

        mom_df = stats_df[['symbol', 'month1ChangePercent',
                           'month3ChangePercent', 'month6ChangePercent', 'year1ChangePercent']]

        # calculate percentiles for each stock over their respective timeframes
        for time in mom_df.iloc[:, 1:5].columns:
            mom_df[time+"_tile"] = mom_df[time].rank(pct=True)

        # get all the percentile columns and average them
        mom_df['avgPercentiles'] = mom_df[[
            col for col in mom_df.columns if "_tile" in col]].mean(axis=1)

        return mom_df


    def get_symbol_info(self, symbols:list[str]) -> pd.DataFrame:
        data = self.api_obj.get_symbol_info(symbols=symbols)
        data_df = pd.DataFrame.from_dict(data.json()).transpose()
        data_df = pd.merge(data_df, data_df['company'].apply(pd.Series), left_index=True, right_index=True)
        data_df = data_df.drop('company', axis=1)
        return data_df

    def get_sectors(self) -> pd.DataFrame:
        """
        Creates a DataFrame of sectors supported by IEX Cloud

        Returns:
            pd.DataFrame: [description]
        """
        sectors = self.api_obj.get_sector_list()
        sectors_df = pd.DataFrame.from_dict(sectors.json())
        return sectors_df

    def get_sector_quotes(self, sector):
        sector_quotes = self.api_obj.get_sector_quotes(sector)
        pdb.set_trace()
        print("here")

    def get_peers(self, symbols):
        _req = self.api_obj._create_request(
            symbols=symbols, data_set=['peers'])
        data = self.api_obj._send_request(request=_req)
        return pd.DataFrame.from_dict(data.json()).transpose()

    def get_advanced_symbol_stats(self, symbols:list[str])->pd.DataFrame:
        """
        Return advanced statistics given a list of symbols.

        Args:
            symbols (list[str]): list of symbols

        Returns:
            pd.DataFrame: DataFrame containing statistics, each row is a symbol
        """
        data = self.api_obj.get_advanced_stats(symbols)
        data_df = pd.DataFrame.from_dict(data.json()).transpose()
        data_df['symbol'] = data_df.index
        data_df = data_df.reset_index(drop=True)
        data_df = pd.merge(
            data_df, data_df['advanced-stats'].apply(pd.Series), left_index=True, right_index=True)
        data_df = data_df.drop('advanced-stats', axis=1)
        return data_df

    def get_symbol_stats(self, symbols: list[str]) -> pd.DataFrame:
        """
        Return simple statistics given a list of symbols.

        Args:
            symbols (list): list of symbols (str)

        Returns:
            pd.DataFrame: DataFrame containing statistics, each row is a symbol.
        """
        data = self.api_obj.get_stats(symbols)
        data_df = pd.DataFrame.from_dict(data.json()).transpose()
        data_df['symbol'] = data_df.index
        data_df = data_df.reset_index(drop=True)
        data_df = pd.merge(data_df, data_df['stats'].apply(
            pd.Series), left_index=True, right_index=True)
        data_df = data_df.drop('stats', axis=1)
        return data_df

    def stream_data(self, symbols):
        data = self.api_obj.stream_symbol(symbols)
        return data


def main(token=None, base_url=None, portfolio_symbols=None, logger=None):
    api_obj = IEXApi(token=api_token, base_url=base_url, logger=logger)

    anal_obj = Analysis(api=api_obj)

    # works
    # stats_df = anal_obj.get_symbol_stats(symbols=portfolio_symbols)
    # sectors = anal_obj.get_sectors()
    # mom_df = anal_obj.momentum_analysis(stats_df)
    # astats_df = anal_obj.get_advanced_symbol_stats(symbols=portfolio_symbols)

    # todo
    df = anal_obj.get_symbol_info(symbols=["NVDA", "PLTR"])
    print(df)

    # sector_quotes = anal_obj.get_sector_quotes("Semiconductors")
    # anal_obj.get_peers(symbols=["NVDA", "CRSP"])
    # stream = anal_obj.stream_data("ATVI")
    # pdb.set_trace()

    return True


def load_env(mode="SandBox", logger=None):

    api_token = None
    base_url = None

    logger.info(f"Loading Env for {mode}")
    sand_api_token = os.getenv("IEX_CLOUD_TOKEN_SAND")
    prod_api_token = os.getenv("IEX_CLOUD_TOKEN")

    if mode == "SandBox":
        api_token = sand_api_token
        base_url = "https://sandbox.iexapis.com"

    elif mode == "Production":
        api_token = prod_api_token
        base_url = "https://cloud.iexapis.com"

    # load in portfolio investments
    with open("portfolio.txt", 'r') as f:
        content = f.read()
    portfolio_symbols = content.split()
    logger.info("Loaded Portfolio")

    return api_token, base_url, portfolio_symbols


if __name__ == "__main__":
    # Create logger
    stream_handler = logging.StreamHandler(sys.stdout)
    file_handler = logging.FileHandler(__name__+".log", mode="a+")
    logging.basicConfig(format='%(asctime)s - %(module)s - %(levelname)s - %(message)s',
                        level=logging.DEBUG, handlers=[file_handler, stream_handler])
    logger = logging.getLogger(__name__)

    # parse args based on our usage
    parser = argparse.ArgumentParser()
    parser.add_argument('--sandbox', '-s', action='store_true',
                        help="Use the Sandbox API Token to IEX")
    parser.add_argument('--production', '-p', action='store_true',
                        help="Use the Production API Token to IEX")
    args = parser.parse_args()

    # logic based on args, defaults to sandbox
    if args.sandbox:
        api_token, base_url, portfolio_symbols = load_env(
            mode="SandBox", logger=logger)
    elif args.production:
        api_token, base_url, portfolio_symbols = load_env(
            mode="Production", logger=logger)
    else:
        api_token, base_url, portfolio_symbols = load_env(
            mode="SandBox", logger=logger)

    main(token=api_token, base_url=base_url,
         portfolio_symbols=portfolio_symbols, logger=logger)
