import os
import re
import sys
import logging
import requests
import datetime
import json
import heapq
import matplotlib.gridspec as gridspec
import matplotlib.pyplot as plt
import pythunder.types
import pythunder.sfit
import pythunder.enums
import pythunder.system
import pythunder.instrument
import pythunder.tickutils as ptu

START_DATE = "20250725"
# Output path
REPORT_PATH = "/publish/future_price_diff"
# Data center
DATA_CENTER = "http://192.168.3.44:70"
# logger
logger = logging.getLogger("arbitrage")

def load_tick_data_by_name(instrument, start_data):
    """
    Load tick data of a given future name
    """
    logger.info("loading data of `%s`" % (instrument))
    start = datetime.datetime.strptime(start_data, "%Y%m%d")
    end = datetime.datetime.today()
    return ptu.load_from_data_center(instrument, start.strftime("%Y%m%d"), end.strftime("%Y%m%d"), DATA_CENTER)

def align_ticks_by_window(tick_serials, window_size):
    class _node:
        def __init__(self, _timestamp, _tick):
            self.timestamp = _timestamp
            self.tick = _tick
            self.unique_name = '%s.%s' % (_tick.tick_type, _tick.instrument_id)
        def __lt__(self, other):
            return self.timestamp < other.timestamp
    window = lambda t : int(t.timestamp / window_size)
    result = dict()
    h = []
    names = set()
    for ticks_list in tick_serials:
        for tick in ticks_list:
            node = _node(tick.timestamp, tick)
            if node.unique_name not in names:
                names.add(node.unique_name)
            h.append(node)
    if len(h) == 0:
        return result
    heapq.heapify(h)
    
    while len(h) != 0:
        this_window = dict()
        window_id = window(h[0])
        while len(h) != 0 and window(h[0]) == window_id:
            node = heapq.heappop(h)
            this_window[node.unique_name] = node.tick
        for i in names.difference(this_window.keys()):
            this_window[i] = None
        for k, v in this_window.items():
            if k not in result:
                result[k] = []
            result[k].append(v)
    return result

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    serial_0 = "sfit.future.bc2509"
    serial_1 = "ibkr.tws.l1.COMEX.447585333"
    serial_2 = "sfit.future.cu2509"
    ticks = []
    ticks.append(load_tick_data_by_name(serial_0, START_DATE))
    ticks.append(load_tick_data_by_name(serial_1, START_DATE))
    ticks.append(load_tick_data_by_name(serial_2, START_DATE))
    serials = align_ticks_by_window(ticks, 1000)
    last_price_0 = [t.last_price * 7.1 * 25000 * 5 / 11 if t is not None else float("NaN") for t in serials[serial_0]]
    last_price_1 = [t.last_price * 5.0 if t is not None else float("NaN")for t in serials[serial_1]]
    last_price_2 = [t.last_price * 7.1 * 25000 * 5 / 11 if t is not None else float("NaN") for t in serials[serial_2]]
    last_price_diff = [last_price_0[i] - last_price_1[i] for i in range(0, len(last_price_0))]
    fig = plt.figure(tight_layout=True, figsize=(32, 18))
    ax = fig.add_subplot()
            
    ax.plot(last_price_0, color='tab:green', label=serial_0)
    ax2 = ax.twinx()
    ax2.plot(last_price_1, color='tab:red',label=serial_1)
    ax3 = ax.twinx()
    ax3.plot(last_price_2, color='tab:blue',label=serial_2)
    ax.legend(prop={'size': 20}, framealpha=0.0, fancybox=False)
    plt.savefig("%s/%s-%s.png" % (REPORT_PATH, serial_0, serial_1), dpi=50, transparent=True)