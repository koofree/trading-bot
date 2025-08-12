import jwt
import hashlib
import uuid
from urllib.parse import urlencode
import requests
import websocket
import json
import logging
from typing import Dict, List, Optional, Callable
from datetime import datetime
import asyncio
import aiohttp

logger = logging.getLogger(__name__)

class UpbitConnector:
    def __init__(self, access_key: str, secret_key: str):
        self.access_key = access_key
        self.secret_key = secret_key
        self.base_url = "https://api.upbit.com/v1"
        self.ws_url = "wss://api.upbit.com/websocket/v1"
        self.ws = None
        self.ws_callbacks = {}
        
    def _generate_auth_header(self, query: Optional[Dict] = None) -> Dict:
        """Generate JWT token for authenticated requests"""
        payload = {
            'access_key': self.access_key,
            'nonce': str(uuid.uuid4()),
        }
        
        if query:
            query_string = urlencode(query).encode()
            m = hashlib.sha512()
            m.update(query_string)
            query_hash = m.hexdigest()
            payload['query_hash'] = query_hash
            payload['query_hash_alg'] = 'SHA512'
            
        jwt_token = jwt.encode(payload, self.secret_key, algorithm='HS256')
        return {'Authorization': f'Bearer {jwt_token}'}
    
    def get_markets(self) -> List[Dict]:
        """Get all available markets"""
        response = requests.get(f"{self.base_url}/market/all")
        return response.json()
    
    def get_ticker(self, markets: List[str]) -> List[Dict]:
        """Get current ticker information for specified markets"""
        params = {'markets': ','.join(markets)}
        response = requests.get(f"{self.base_url}/ticker", params=params)
        return response.json()
    
    def get_orderbook(self, markets: List[str]) -> List[Dict]:
        """Get orderbook for specified markets"""
        params = {'markets': ','.join(markets)}
        response = requests.get(f"{self.base_url}/orderbook", params=params)
        return response.json()
    
    def get_candles(self, market: str, interval: str = 'minutes', 
                   unit: int = 1, count: int = 200) -> List[Dict]:
        """
        Fetch historical candle data
        interval: 'minutes', 'days', 'weeks', 'months'
        unit: 1, 3, 5, 15, 30, 60, 240 (for minutes)
        """
        endpoint = f"{self.base_url}/candles/{interval}/{unit}"
        params = {'market': market, 'count': count}
        response = requests.get(endpoint, params=params)
        return response.json()
    
    def get_recent_trades(self, market: str, count: int = 100) -> List[Dict]:
        """Get recent trades for a market"""
        params = {'market': market, 'count': count}
        response = requests.get(f"{self.base_url}/trades/ticks", params=params)
        return response.json()
    
    def get_accounts(self) -> List[Dict]:
        """Get account balance information"""
        headers = self._generate_auth_header()
        response = requests.get(f"{self.base_url}/accounts", headers=headers)
        return response.json()
    
    def get_orders(self, market: Optional[str] = None, state: str = 'wait') -> List[Dict]:
        """
        Get order list
        state: wait, watch, done, cancel
        """
        query = {'state': state}
        if market:
            query['market'] = market
            
        headers = self._generate_auth_header(query)
        response = requests.get(f"{self.base_url}/orders", 
                               params=query, headers=headers)
        return response.json()
    
    def place_order(self, market: str, side: str, volume: float, 
                   price: Optional[float] = None, ord_type: str = 'limit') -> Dict:
        """
        Place buy/sell order
        side: 'bid' (buy) or 'ask' (sell)
        ord_type: 'limit', 'price' (market buy), 'market' (market sell)
        """
        data = {
            'market': market,
            'side': side,
            'ord_type': ord_type,
        }
        
        if ord_type == 'limit':
            data['price'] = str(price)
            data['volume'] = str(volume)
        elif ord_type == 'price':
            data['price'] = str(price)
        elif ord_type == 'market':
            data['volume'] = str(volume)
            
        headers = self._generate_auth_header(data)
        response = requests.post(f"{self.base_url}/orders", 
                                data=data, headers=headers)
        
        if response.status_code == 201:
            return {'status': 'success', 'data': response.json()}
        else:
            return {'status': 'failed', 'error': response.text}
    
    def cancel_order(self, uuid: str) -> Dict:
        """Cancel an order"""
        data = {'uuid': uuid}
        headers = self._generate_auth_header(data)
        response = requests.delete(f"{self.base_url}/order", 
                                  params=data, headers=headers)
        return response.json()
    
    def start_websocket(self, markets: List[str], callbacks: Dict[str, Callable]):
        """
        Start WebSocket connection for real-time data
        callbacks: Dict with keys 'ticker', 'trade', 'orderbook'
        """
        self.ws_callbacks = callbacks
        
        def on_message(ws, message):
            data = json.loads(message)
            event_type = data.get('type', '')
            
            if event_type == 'ticker' and 'ticker' in self.ws_callbacks:
                self.ws_callbacks['ticker'](data)
            elif event_type == 'trade' and 'trade' in self.ws_callbacks:
                self.ws_callbacks['trade'](data)
            elif event_type == 'orderbook' and 'orderbook' in self.ws_callbacks:
                self.ws_callbacks['orderbook'](data)
                
        def on_error(ws, error):
            logger.error(f"WebSocket error: {error}")
            
        def on_close(ws, close_status_code, close_msg):
            logger.info(f"WebSocket closed: {close_msg}")
            
        def on_open(ws):
            # Subscribe to markets
            subscribe_data = [
                {"ticket": str(uuid.uuid4())},
                {
                    "type": "ticker",
                    "codes": markets,
                    "isOnlyRealtime": True
                },
                {"format": "DEFAULT"}
            ]
            ws.send(json.dumps(subscribe_data))
            logger.info(f"Subscribed to markets: {markets}")
            
        self.ws = websocket.WebSocketApp(
            self.ws_url,
            on_open=on_open,
            on_message=on_message,
            on_error=on_error,
            on_close=on_close
        )
        
        self.ws.run_forever()
    
    def stop_websocket(self):
        """Stop WebSocket connection"""
        if self.ws:
            self.ws.close()
            
    async def async_get_ticker(self, markets: List[str]) -> List[Dict]:
        """Async version of get_ticker"""
        async with aiohttp.ClientSession() as session:
            params = {'markets': ','.join(markets)}
            async with session.get(f"{self.base_url}/ticker", params=params) as resp:
                return await resp.json()
                
    async def async_get_candles(self, market: str, interval: str = 'minutes', 
                               unit: int = 1, count: int = 200) -> List[Dict]:
        """Async version of get_candles"""
        async with aiohttp.ClientSession() as session:
            endpoint = f"{self.base_url}/candles/{interval}/{unit}"
            params = {'market': market, 'count': count}
            async with session.get(endpoint, params=params) as resp:
                return await resp.json()