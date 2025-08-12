import enum
import threading
from ctypes import *
import time
from typing import List, Dict
from pathlib import PurePath, Path

from pendulum import DateTime, parse

# Determine the directory where the current Python script resides
current_dir = Path(__file__).resolve().parent.parent

# Build path to the shared library relative to the script
# Adjust folder names to match your project structure
so_path = PurePath(current_dir, "cpp", "build", "libexecutor.so")

# Load the shared library
lib = CDLL(str(so_path))

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
            print("\n=== Market Depth Cache ===")
            print("--- BID ---")
            for md in symbol_cache.bid_market_depth:
                if md.symbol:  # only print populated entries
                    print(f"{md.symbol} | Pos: {md.position} | Side: BID | Price: {md.px} | Qty: {md.qty} "
                          f"| Maker: {md.market_maker} | SmartDepth: {md.is_smart_depth} "
                          f"| CumNot: {md.cumulative_notional} | CumQty: {md.cumulative_qty} "
                          f"| CumAvgPx: {md.cumulative_avg_px}")
            print("--- ASK ---")
            for md in symbol_cache.ask_market_depth:
                if md.symbol:
                    print(f"{md.symbol} | Pos: {md.position} | Side: ASK | Price: {md.px} | Qty: {md.qty} "
                          f"| Maker: {md.market_maker} | SmartDepth: {md.is_smart_depth} "
                          f"| CumNot: {md.cumulative_notional} | CumQty: {md.cumulative_qty} "
                          f"| CumAvgPx: {md.cumulative_avg_px}")
        time.sleep(5)  # slow down output


def market_depth_callback(mes_p):
    try:
        md = mes_p[0]
        # Convert C strings to Python strings
        symbol = md.symbol_.decode() if md.symbol_ else ''
        exch_time = md.exch_time_.decode() if md.exch_time_ else ''
        arrival_time = md.arrival_time_.decode() if md.arrival_time_ else ''
        side = md.side_.decode() if md.side_ else ''
        market_maker = md.market_maker_.decode() if md.market_maker_ else ''

        # Print a full snapshot of the struct
        print("\n--- Market Depth Update ---")
        print(f"Symbol: {symbol}")
        print(f"Exchange Time: {exch_time}")
        print(f"Arrival Time: {arrival_time}")
        print(f"Side: {side}")
        print(f"Price: {md.px_} (Set: {md.is_px_set_})")
        print(f"Quantity: {md.qty_} (Set: {md.is_qty_set_})")
        print(f"Position: {md.position_}")
        print(f"Market Maker: {market_maker} (Set: {md.is_market_maker_set_})")
        print(f"Is Smart Depth: {md.is_smart_depth_} (Set: {md.is_is_smart_depth_set_})")
        print(f"Cumulative Notional: {md.cumulative_notional_} (Set: {md.is_cumulative_notional_set_})")
        print(f"Cumulative Quantity: {md.cumulative_qty_} (Set: {md.is_cumulative_qty_set_})")
        print(f"Cumulative Avg Price: {md.cumulative_avg_px_} (Set: {md.is_cumulative_avg_px_set_})")
        print("---------------------------")

        # Also update cache
        symbol_cache = SymbolCacheContainer.get_symbol_cache(symbol)
        mkt_depths = symbol_cache.bid_market_depth if side == 'B' else symbol_cache.ask_market_depth
        mkt_depth = mkt_depths[md.position_]

        mkt_depth.symbol = symbol
        mkt_depth.arrival_time = convert_str_to_datetime(arrival_time) if arrival_time else None
        mkt_depth.exch_time = convert_str_to_datetime(exch_time) if exch_time else None
        mkt_depth.side = TickType.BID if side == 'B' else TickType.ASK
        mkt_depth.px = md.px_
        mkt_depth.qty = md.qty_
        mkt_depth.position = md.position_
        mkt_depth.market_maker = market_maker
        mkt_depth.is_smart_depth = md.is_smart_depth_
        mkt_depth.cumulative_notional = md.cumulative_notional_
        mkt_depth.cumulative_qty = md.cumulative_qty_
        mkt_depth.cumulative_avg_px = md.cumulative_avg_px_

    except Exception as e:
        print(f"Error in callback: {e}")
    return 0


SymbolCacheContainer.add_symbol_cache_for_symbol("CB_Sec_1")
a = market_depth_callback_type(market_depth_callback)
lib.register_mkt_depth_fp(a)

thread = threading.Thread(target=market_depth_consumer, daemon=True)
thread.start()

lib.process_market_depth()

time.sleep(5)