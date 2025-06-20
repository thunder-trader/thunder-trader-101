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

# Start data
START_DATE = "20250618"
# Output path
REPORT_PATH = "/publish/future_price_diff"
# Data center
DATA_CENTER = "http://192.168.3.44:70"

logger = logging.getLogger("arbitrage_in_day")


def load_tick_data_by_name(instrument, start_data):
    """
    Load tick data of a given future name
    """
    logger.info("loading data of `%s`" % (instrument))
    start = datetime.datetime.strptime(start_data, "%Y%m%d")
    end = datetime.datetime.today()
    return ptu.load_from_data_center(instrument, start.strftime("%Y%m%d"), end.strftime("%Y%m%d"), DATA_CENTER)

if __name__ == "__main__":
    slot_0 = "sfit.future.RM508"
    slot_1 = "sfit.future.RM509"
    if len(sys.argv) == 3:
        slot_0 = sys.argv[1]
        slot_1 = sys.argv[2]
    ticks_0 = load_tick_data_by_name(slot_0, START_DATE)
    for t in ticks_0:
        t.slot = 0
    ticks_1 = load_tick_data_by_name(slot_1, START_DATE)
    for t in ticks_1:
        t.slot = 1
    ticks_list = []
    ticks_list = ptu.merge(ticks_list, ticks_0)
    ticks_list = ptu.merge(ticks_list, ticks_1)
    ticks = ptu.align(ticks_list)
    if len(ticks[0]) != len(ticks[1]):
        exit()
    size = len(ticks[0])
    a_ask = [ticks[0][i].get_ask_price(0) - ticks[1][i].get_bid_price(0) for i in range(0, size)]
    a_bid = [ticks[0][i].get_bid_price(0) - ticks[1][i].get_ask_price(0) for i in range(0, size)]
    for i in range(0, len(a_ask)):
        if abs(a_ask[i]) > 100:
            a_ask[i] = float("nan")
    for i in range(0, len(a_bid)):
        if abs(a_bid[i]) > 100:
            a_bid[i] = float("nan")
    fig = plt.figure(tight_layout=True, figsize=(1024, 18))
    ax = fig.add_subplot()
            
    ax.plot(a_ask, color='tab:red', label="ask_price", linewidth=0.3)
    ax.plot(a_bid, color='tab:green', label="bid_price", linewidth=0.3)
    ax.legend(prop={'size': 20}, framealpha=0.0, fancybox=False)
    plt.savefig("%s/detail-%s-%s.png" % (REPORT_PATH, slot_0, slot_1), dpi=80, transparent=True)
