import os
import re
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

# Output path
REPORT_PATH = "/publish/future_price_diff"
# Data center
DATA_CENTER = "http://192.168.3.44:70"
# Configuration which described instruments need to be calculate
CONFIGURATION = """[{"enable":1,"sfit":"a"},{"enable":1,"sfit":"b"},{"enable":1,"sfit":"c"},{"enable":1,"sfit":"ag"}]"""

def load_tick_data(future_type, start_data):
    """
    Load tick data of a given future type
    """
    logging.info("loading data of `%s*`" % (future_type))
    result = dict()
    start = datetime.datetime.strptime(start_data, "%Y%m%d")
    end = datetime.datetime.today()
    instrument_ids = []
    # Load instrument meta data from /thunder-data/instruments.conf
    # This data file will be update every day from thunder-trader.com
    instrument_records = pythunder.system.load_instrument_information_from_file("/thunder-data/instruments.config")
    # Find all instrument names of this specified future type
    pattern = "%s\\d+$" % (future_type)
    for name, value in instrument_records.items():
        if (re.match(pattern, value.get_instrument_id())):
            instrument_ids.append(value.get_unique_name())
    logging.info("instrument list of `%s` is `%s`" % (future_type, instrument_ids))
    # Load tick data from data center for every instrument
    for item in instrument_ids:
        result[item] = ptu.load_from_data_center(item, start.strftime("%Y%m%d"), end.strftime("%Y%m%d"), DATA_CENTER)
    return result


def merge(data):
    h = []
    names = set(data.keys())
    for k, v in data.items():
        for tick in v:
            heapq.heappush(h, (tick.timestamp, "%s.%s" % (tick.tick_type, tick.instrument_id), tick.last_price, tick.datetime))
    heapq.heapify(h)
    result = dict()
    timestamp = []
    window = lambda t : int(t[0] / 60000)

    while len(h) != 0:
        sample = dict()
        tick = heapq.heappop(h)
        sample[tick[1]] = tick[2]
        window_index = window(tick)
        while len(h) != 0 and window(h[0]) == window_index:
            tick = heapq.heappop(h)
            sample[tick[1]] = tick[2]
        for i in names.difference(sample.keys()):
            sample[i] = float("nan")

        for k, v in sample.items():
            if k not in result:
                result[k] = []
            result[k].append(v)
        timestamp.append(window_index * 60000)
    return result


def plot(left_plot, serials, slot0, slot1):
    logging.info("ploting price diff of %s & %s" % (slot0, slot1))
    for k, v in serials.items():
        if k == slot0:
            left_plot.plot(v, linewidth=3, alpha=1.0, color='tab:green', label=k)
        elif k == slot1:
            left_plot.plot(v, linewidth=3, alpha=1.0, color='tab:blue', label=k)
        else:
            left_plot.plot(v, linewidth=1, alpha=0.3)
    right_plot = left_plot.twinx()
    diff = []
    size = len(serials[slot0])
    for i in range(0, size):
        diff.append(serials[slot0][i] - serials[slot1][i])
    right_plot.plot(diff, color='tab:red', label='arbitrage')
    left_plot.legend(prop={'size': 60}, framealpha=0.0, fancybox=False)


def plot_helper(name_prefix, serials, plot_list):
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
        plot(left_plot, serials, plot_list[i][0], plot_list[i][1])
    plt.savefig("%s/%s.png" % (REPORT_PATH, name_prefix), dpi=50, transparent=True)
    plt.close()


def read_configuration(conf):
    """
    Read arbitrage configuration
    """
    conf_list = json.loads(conf)
    result = set()
    for conf in conf_list:
        if "enable" in conf and conf["enable"] == 0:
            continue
        if "sfit" in conf:
            result.add(conf['sfit'])
    return result


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    if not os.path.exists(REPORT_PATH):
        os.makedirs(REPORT_PATH)
    future_types = read_configuration(CONFIGURATION)
    logging.info(future_types)
    for type in future_types:
        ticks = load_tick_data(type, "20250501")
        print(ticks.keys())
        serials = merge(ticks)
        names = list(serials.keys())
        names.sort()
        plot_list = []
        for i in range(0, len(names) - 1):
            plot_list.append((names[i], names[i + 1]))
        plot_helper(type, serials, plot_list)