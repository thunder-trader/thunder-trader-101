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
import numpy as np

class serial_t:
    def __init__(self, original_ticks_serial):
        self.last_price = [t.last_price if t is not None else float('NaN') for t in original_ticks_serial]
        self.ask_price = [t.get_ask_price(0) if t is not None else float('NaN') for t in original_ticks_serial]
        self.bid_price = [t.get_bid_price(0) if t is not None else float('NaN') for t in original_ticks_serial]


class price_diff_matrix_t:
    @staticmethod
    def serial_filer(serial):
        max_v = np.nanpercentile(serial, 95)
        min_v = np.nanpercentile(serial, 5)
        for i in range(0, len(serial)):
            if serial[i] > max_v or serial[i] < min_v:
                serial[i] = float('NaN')

    @staticmethod
    def plot_one(main_plot, serials, slot0, slot1):
        logger = logging.getLogger("price_diff_matrix")
        logger.info("ploting price diff of %s & %s" % (slot0, slot1))
        for k, v in serials.items():
            if k == slot0:
                main_plot.plot(v.last_price, linewidth=3, alpha=1.0, color='tab:blue', label=k)
            elif k == slot1:
                main_plot.plot(v.last_price, linewidth=3, alpha=1.0, color='tab:blue', label=k)
            else:
                main_plot.plot(v.last_price, linewidth=1, alpha=0.3, color='tab:orange')
        right_plot = main_plot.twinx()
        diff_ask = []
        diff_bid = []
        size = len(serials[slot0].last_price)
        for i in range(0, size):
            diff_ask.append(serials[slot0].ask_price[i] - serials[slot1].bid_price[i])
            diff_bid.append(serials[slot0].bid_price[i] - serials[slot1].ask_price[i])
        price_diff_matrix_t.serial_filer(diff_ask)
        price_diff_matrix_t.serial_filer(diff_bid)
        right_plot.plot(diff_ask, color='tab:red', label='diff_ask')
        right_plot.plot(diff_bid, color='tab:green', label='diff_bid')
        main_plot.legend(prop={'size': 60}, framealpha=0.0, fancybox=False)

    @staticmethod
    def plot_helper(file_name, serials, plot_list):
        logger = logging.getLogger("price_diff_matrix")
        MAX_COLUME = 3
        size = len(plot_list)
        if size == 0:
            return
        if size >= MAX_COLUME and size % MAX_COLUME == 0:
            MAX_ROW = int(size / MAX_COLUME)
        else:
            MAX_ROW = int(size / MAX_COLUME) + 1
        fig = plt.figure(tight_layout=True, figsize=(25 * MAX_COLUME, 15 * MAX_ROW))
        gs = gridspec.GridSpec(MAX_ROW, MAX_COLUME)
        for i in range(0, len(plot_list)):
            row = int(i / MAX_COLUME)
            col = i % MAX_COLUME
            left_plot = fig.add_subplot(gs[row, col])
            price_diff_matrix_t.plot_one(left_plot, serials, plot_list[i][0], plot_list[i][1])
        plt.savefig(file_name, dpi=80, transparent=False)
        plt.close()
        logger.info("instrument report `%s` is saved" % (file_name))

    @staticmethod
    def price_diff_matrix(filename, instruments_list, start_date, end_date, data_center):
        tick_serials = []
        for item in instruments_list:
            tick_serials.append(ptu.load_from_data_center(item, start_date, end_date, data_center))
        serials = ptu.align_ticks_by_window(tick_serials, 5000)
        for key in serials.keys():
            serials[key] = serial_t(serials[key])
        names = list(serials.keys())
        names.sort()
        plot_list = []
        for i in range(0, len(names)):
            for t in range(i + 1, len(names)):
                plot_list.append((names[i], names[t]))
        price_diff_matrix_t.plot_helper(filename, serials, plot_list)


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    logHandler = logging.FileHandler("/publish/arbitrage.%s.log" % (datetime.datetime.now().date()))
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    logHandler.setFormatter(formatter)
    logger = logging.getLogger("price_diff_matrix")
    logger.addHandler(logHandler)
    START_DATE = "20250707"
    # Output path
    REPORT_PATH = "/publish/future_price_diff"
    # Data center
    DATA_CENTER = "http://192.168.3.44:70"
    # Configuration which described instruments need to be calculate.
    hg = [
        "ibkr.tws.l1.COMEX.651096940",
        "ibkr.tws.l1.COMEX.447585333",
        "ibkr.tws.l1.COMEX.662922793",
        "ibkr.tws.l1.COMEX.668631619",
		"ibkr.tws.l1.COMEX.447766922"
    ]
    cu = [
        "sfit.future.c2508",
        "sfit.future.c2509",
        "sfit.future.c2510",
        "sfit.future.c2511",
		"sfit.future.c2512",
    ]
    ZC = [
        "ibkr.tws.l1.CBOT.602619745",
        "ibkr.tws.l1.CBOT.532513373",
        "ibkr.tws.l1.CBOT.671574012"
    ]

    price_diff_matrix_t.price_diff_matrix("%s/ZC.png" % (REPORT_PATH), ZC, '20250801', '20250805', DATA_CENTER)
    

    