#include <iostream>
#include <thread>
#include <cstring> // For strlen

struct PyMarketDepth {
	const char* symbol_;
	const char* exch_time_;
	const char* arrival_time_;
	char side_;
	double px_;
	bool is_px_set_;
	int64_t qty_;
	bool is_qty_set_;
	int32_t position_;
	const char* market_maker_;
	bool is_market_maker_set_;
	bool is_smart_depth_;
	bool is_is_smart_depth_set_;
	double cumulative_notional_;
	bool is_cumulative_notional_set_;
	int64_t cumulative_qty_;
	bool is_cumulative_qty_set_;
	double cumulative_avg_px_;
	bool is_cumulative_avg_px_set_;
};

extern "C" {

    using mkt_depth_fp_t = int(*)(PyMarketDepth const*);
    mkt_depth_fp_t mkt_depth_fp{nullptr};

    void register_mkt_depth_fp(mkt_depth_fp_t mdfp) {
        mkt_depth_fp = mdfp;
    }

    void process_market_depth() {
        PyMarketDepth market_depth{"CB_Sec_1", "2024-10-01T21:05:44.667+00:00",
        	"2024-10-01T21:05:44.667+00:00", 'B', 1.1, true, 10,
        	true, 1, "", true, false,
        	true, 10.1, true, 1,
        	true, 10.1, true};
    	mkt_depth_fp(&market_depth);
    }

}
