import sys
import requests
import pdb
import logging
import os
from typing import Union


class IEXApi():
    """
    Object to interact with the API. Requires an account at https://iexcloud.io/
    """

    def __init__(self,
                 token: Union[str, None] = os.getenv("IEX_CLOUD_TOKEN_SAND"),
                 base_url: Union[str, None] = "https://sandbox.iexapis.com",
                 logger=None):
        """
        Class to interact with IEX Cloud API.

        Args:
            token (Union[str,None], optional): Personal Token required to interact with API. Defaults to os.getenv("IEX_CLOUD_TOKEN_SAND").
            base_url (Union[str,None], optional): Base URL to send requests. Defaults to "https://sandbox.iexapis.com".
            logger (logging.Logger, optional): Logger to be used within the class. Defaults to None.
        """

        if logger is None:
            logger = logging.getLogger(__name__)

        self.logger = logger
        self.token = token
        self.base_url = base_url
        self.logger.info(f"Loaded API w/ base_url = {self.base_url}")

    def get_symbol_info(self, symbols: list[str]) -> requests.Response:
        """
        Get general information about the symbol.

        Args:
            symbol (str): Symbol of interest.

        Returns:
            requests.Response: Requests object returned by API.
        """
        req = self._create_request(request_type='info', symbols=symbols, data_set=['company'])
        data = self._send_request(req)
        return data

    def get_stats(self, symbols: list[str]) -> Union[requests.Response, None]:
        """
        Gets statistics for each symbol

        Args:
            symbols (list[str]): Stock symbols of interest.

        Returns:
            Union[requests.Response, None]: Requests object returned by API.
        """
        # API should have < 100 symbols
        if len(symbols) > 100:
            self.logger.error(f"len(symbols) = {len(symbols)} > 100")
            return None

        req = self._create_request(request_type="stat",
                                   symbols=symbols, data_set=["stats", "price"])
        data = self._send_request(req)
        return data

    def get_advanced_stats(self, symbols: list[str]) -> Union[requests.Response, None]:
        """
        Request advanced statistics given a list of symbols.

        Args:
            symbols (list[str]): Stock symbols of interest.

        Returns:
            Union[requests.Response, None]: Requests object returned by API.
        """
        if len(symbols) > 100:
            self.logger.error(f"len(symbols) = {len(symbols)} > 100")
            return None

        req = self._create_request(request_type="stat",
                                   symbols=symbols, data_set=['advanced-stats'])
        data = self._send_request(req)
        return data

    # def get_sector_quotes(self, sector):
    #     req = self._create_request(sector=sector)
    #     data = self._send_request(req)
    #     return data

    def get_sector_list(self) -> requests.Response:
        """
        Request list of sectors from API.

        Returns:
            requests.Response: Requests object returned by API.
        """
        req = self._create_request(request_type="sector_list")
        data = self._send_request(req)
        return data

    # def stream_symbol(self, symbol):
    #     pdb.set_trace()
    #     symbol = symbol.split(",")
    #     req = self._create_request(symbols=symbol, stream=True)

    def _create_request(self,
                        request_type: str,
                        symbols: list[str] = None,
                        data_set: list[str] = None,
                        custom: str = None,
                        *args, **kwargs
                        ) -> str:
        """
        Create the URL request to pass to self._send_request(), w/o the token.

        This function serves at the catch all to interact with the API, and will essentially grow
        with usage.

        Args:
            symbols (list, optional): Stock symbols to query. Defaults to None.
            data_set (list, optional): Data set to query (e.g. advanced, stats, daily, etc). Defaults to None.
            custom (str, optional): Custom URL request that overides the arguments. Defaults to None.

        Returns:
            string: String of the URL request.
        """


        try:
            if request_type == "stat" or request_type == "info":
                # Some type checking to make sure that symbols is a list of symbols, since we are only using batch requests
                if not isinstance(symbols,  list) or symbols  is None or \
                   not isinstance(data_set, list) or data_set is None:
                    raise TypeError

                else:
                    joined_data_set = ','.join(data_set) 
                    joined_symbols = ','.join(symbols)
                    return f"{self.base_url}/stable/stock/market/batch?symbols={joined_symbols}&types={joined_data_set}&"

            # elif sector is not None:
                # batch_api_call_url = f"{self.base_url}/stable/stock/market/collection/sector?collectionName={sector}&"

            # elif sector_list is not None and sector_list:
            #     batch_api_call_url = f"{self.base_url}/stable/ref-data/sectors?"

            elif request_type == "sector_list":
                return f"{self.base_url}/stable/ref-data/sectors?"
            else:
                raise NotImplementedError

        except Exception as e:
            self.logger.error(f"Received Error {e}", exc_info=True)
            return "fuck off"

    def _send_request(self, request: str) -> requests.Response:
        """
        Sends request to IEX API

        Args:
            request (str): Raw string to be send directly to API

        Returns:
            requests.Response : Request object containing the results.
        """
        request += f"token={self.token}"
        self.logger.info(f"Sending Request - {request}")
        data = requests.get(request)

        self.logger.info(f"Request Status Code - {data.status_code}")
        return data

    def _chunk_symbols_list(self, symbols, n):
        """
        Chunk list of symbols into groups of 100 to help w/ API performance.

        Args:
            symbols (list): List of strings, each string is a symbol/ticker
        """

        for i in range(0, len(symbols), n):
            yield symbols[i:i+n]
