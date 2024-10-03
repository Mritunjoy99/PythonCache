import enum
import threading
from ctypes import *
import time
from typing import List, Dict

from pendulum import DateTime, parse

# Load the shared library
lib = CDLL('/home/subham/Desktop/test/PythonCache/cpp/cmake-build-debug/libexecutor.so')

def convert_str_to_datetime(date_str: str) -> DateTime:
    return parse(date_str)


class MarketDepth(Structure):
    _fields_ = (
        ('symbol_', c_char_p), ('exch_time_', c_char_p), ('arrival_time_', c_char_p), ('side_', c_char),
        ('px_', c_double), ('is_px_set_', c_bool), ('qty_', c_int64), ('is_qty_set_', c_bool),
        ('position_', c_int32), ('market_maker_', c_char_p), ('is_market_maker_set_', c_bool),
        ('is_smart_depth_', c_bool), ('is_is_smart_depth_set_', c_bool),
        ('cumulative_notional_', c_double), ('is_cumulative_notional_set_', c_bool),
        ('cumulative_qty_', c_int64), ('is_cumulative_qty_set_', c_bool),
        ('cumulative_avg_px_', c_double), ('is_cumulative_avg_px_set_', c_bool)
    )

    def __str__(self):
        return f"MD: symbol={self.symbol_}, px={self.px_}, qty={self.qty_}, side={self.side_}"


market_depth_callback_type = CFUNCTYPE(c_int, POINTER(MarketDepth))

class TickType(enum.Enum):
    BID = enum.auto()
    ASK = enum.auto()


class ExtendedMarketDepth:
    def __init__(self):
        self.symbol: str | None = None
        self.exch_time: DateTime | None = None
        self.arrival_time: DateTime | None = None
        self.side: TickType | None = None
        self.px: float | None = None
        self.qty: int | None = None
        self.position: int | None = None
        self.market_maker: str | None = None
        self.is_smart_depth: bool | None = None
        self.cumulative_notional: float | None = None
        self.cumulative_qty: int | None = None
        self.cumulative_avg_px: float | None = None


class SymbolCache:
    def __init__(self):
        self.bid_market_depth: List[ExtendedMarketDepth] = [] * 10
        self.ask_market_depth: List[ExtendedMarketDepth] = [] * 10

        for i in range(10):
            self.bid_market_depth.append(ExtendedMarketDepth())
            self.ask_market_depth.append(ExtendedMarketDepth())


class SymbolCacheContainer:
    symbol_to_symbol_cache_dict: Dict[str, SymbolCache] = {}
    semaphore = threading.Semaphore(0)

    @staticmethod
    def release_notify_semaphore():
        SymbolCacheContainer.semaphore.release()

    @staticmethod
    def acquire_notify_semaphore():
        SymbolCacheContainer.semaphore.acquire()

    @classmethod
    def get_symbol_cache(cls, symbol: str) -> SymbolCache | None:
        symbol_cache = cls.symbol_to_symbol_cache_dict.get(symbol)
        return symbol_cache

    @classmethod
    def add_symbol_cache_for_symbol(cls, symbol: str) -> SymbolCache:
        symbol_cache = cls.symbol_to_symbol_cache_dict.get(symbol)
        if symbol_cache is None:
            symbol_cache = SymbolCache()
            cls.symbol_to_symbol_cache_dict[symbol] = symbol_cache
            print(f'Added Container Obj for symbol: {symbol}')
            return symbol_cache
        else:
            print(f"SymbolCache for {symbol=} already exists - passing existing object to caller of "
                            "add_symbol_cache_for_symbol")
            return symbol_cache

def market_depth_consumer():
    while True:
        for symbol_cache in SymbolCacheContainer.symbol_to_symbol_cache_dict.values():
            for md in symbol_cache.bid_market_depth:
                print(f'symbol: {md.symbol}, depth: {md.position}')
            for md in symbol_cache.ask_market_depth:
                print(f'symbol: {md.symbol} depth: {md.position}')

def market_depth_callback(mes_p):
    try:
        md = mes_p[0]
        print(mes_p)
        symbol_cache: SymbolCache = SymbolCacheContainer.get_symbol_cache(md.symbol_.decode())
        mkt_depths: List[
            ExtendedMarketDepth] = symbol_cache.bid_market_depth if 'B' == md.side_.decode() else symbol_cache.ask_market_depth
        mkt_depth: ExtendedMarketDepth = mkt_depths[md.position_]
        try:
            mkt_depth.symbol = md.symbol_.decode()
            mkt_depth.arrival_time = convert_str_to_datetime(md.arrival_time_.decode())
            mkt_depth.exch_time = convert_str_to_datetime(md.exch_time_.decode())
            mkt_depth.side = TickType.BID if md.side_.decode() == 'B' else TickType.ASK
            mkt_depth.px = md.px_ if md.is_px_set_ else 0.0
            mkt_depth.qty = md.qty_ if md.is_qty_set_ else 0
            mkt_depth.position = md.position_
            mkt_depth.market_maker = md.market_maker_.decode() if md.market_maker_ else ''
            mkt_depth.is_smart_depth = md.is_smart_depth_ if md.is_is_smart_depth_set_ else False
            mkt_depth.cumulative_notional = md.cumulative_notional_ if md.is_cumulative_notional_set_ else 0.0
            mkt_depth.cumulative_qty = md.cumulative_qty_ = md.cumulative_qty_ if md.is_cumulative_qty_set_ else 0
            mkt_depth.cumulative_avg_px = md.cumulative_avg_px_ if md.is_cumulative_avg_px_set_ else 0.0
        except Exception as e:
            print(f'Exception: {e}')
    except Exception as e:
        print(e)
    return 0

SymbolCacheContainer.add_symbol_cache_for_symbol("CB_Sec_1")
a = market_depth_callback_type(market_depth_callback)
lib.register_mkt_depth_fp(a)

thread = threading.Thread(target=market_depth_consumer, daemon=True)
thread.start()

lib.process_market_depth()

time.sleep(50)