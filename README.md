***

# **C++ ↔ Python Market Depth Callback Example**

## **Overview**
This project demonstrates **interfacing between C++ and Python** using a **shared library (`.so`)** and the `ctypes` library in Python.

The C++ side:
- Defines a `PyMarketDepth` structure for representing *market depth* data.
- Allows Python to **register a callback** (`register_mkt_depth_fp`) that will be called when new market depth data is available.
- Generates a **sample market depth object** and sends it to Python via `process_market_depth()`.

The Python side:
- Loads the compiled C++ shared library (`libexecutor.so`) using `ctypes`.
- Defines a **matching struct** for `PyMarketDepth` so Python can interpret C++ memory correctly.
- Implements a **callback function** (`market_depth_callback`) to receive and process the data from C++.
- Maintains a **symbol cache** containing the latest bid/ask snapshots.
- Starts a **consumer thread** that periodically prints the stored market depth data.

***

## **Directory Structure**
```
PythonCache/
│
├── cpp/
│   ├── executor.cpp         # C++ shared library code
│   ├── CMakeLists.txt       # Build settings for CMake
│   └── build/               # Build output (libexecutor.so)
│
├── python/
│   └── symbol_cache.py              # Python code using ctypes
│
└── README.md
```

***

## **Step-by-Step How It Works**

### **1. C++ Flow**
1. The struct **`PyMarketDepth`** holds:
    - Symbol, exchange time, arrival time
    - Price, quantity, position
    - Market maker, cumulative stats
2. `register_mkt_depth_fp` stores the Python callback pointer in a global variable.
3. `process_market_depth` creates a **dummy market depth update** and sends it to Python through the registered callback.

### **2. Python Flow**
1. Loads `libexecutor.so` using `ctypes.CDLL`.
2. Defines a struct `MarketDepth` with matching layout/alignment to `PyMarketDepth`.
3. Creates a `CFUNCTYPE` callback matching the C++ signature (`int callback(const PyMarketDepth*)`).
4. Registers the callback with `lib.register_mkt_depth_fp`.
5. Defines a **symbol cache** (`SymbolCacheContainer`) to store latest bid/ask depths for each symbol.
6. Starts a **market depth consumer thread** that prints all cached bid/ask data every 5 seconds.
7. Calls `lib.process_market_depth()` to trigger one example update.

***

## **Prerequisites**
- **C++17 or later**
- **CMake 3.26+**
- **Python 3.10+**
- Python dependencies:
  ```bash
  pip install pendulum
  ```

***

## **Build Instructions**

### **1. Compile C++ Library**
From the `cpp/` directory:

```bash
mkdir build
cd build
cmake ..
make
```

This will generate:
```
build/libexecutor.so
```

***

### **2. Run Python Script**
From the `python/` directory:

```bash
python symbol_cache.py
```

You should see:
- A log message adding the symbol cache:
  ```
  Added Container Obj for symbol: CB_Sec_1
  ```
- A **market depth update** printed by the callback:
  ```
  --- Market Depth Update ---
  Symbol: CB_Sec_1
  Exchange Time: 2024-10-01T21:05:44.667+00:00
  Arrival Time: 2024-10-01T21:05:44.667+00:00
  Side: B
  Price: 1.1 (Set: True)
  Quantity: 10 (Set: True)
  Position: 1
  Market Maker:  (Set: True)
  Is Smart Depth: False (Set: True)
  Cumulative Notional: 10.1 (Set: True)
  Cumulative Quantity: 1 (Set: True)
  Cumulative Avg Price: 10.1 (Set: True)
  ---------------------------
  ```
- After ~5 seconds, the **consumer thread** will display cached data.

***

## **Key Concepts Demonstrated**
- **ctypes struct mapping** — Ensuring Python struct matches C++ memory layout.
- **Callback registration** — Passing a Python function to C++ as a function pointer.
- **Thread-safe caching** — Using a Python `threading.Semaphore` to manage access (could be extended in future).
- **Bid/Ask separation** — Separate lists for bid and ask market depth.

***

## **Notes**
- Currently, `process_market_depth()` sends **one** hardcoded update. For continuous streaming, you would implement a loop or background thread on the C++ side.
- Ensure you keep the Python callback reference in a **global variable** so it is not garbage collected while C++ may still call it.

***
