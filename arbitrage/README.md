# Arbitrage



- Generate configuration

```shell
# python3 show_instruments.py > config.json
```

And make some symbols to enable:1

- Run

```shell
# python3 arbitrage_plot.py config.json
```

- Run by crontab

```shell
0 19 * * * cd /thunder-trader-101/arbitrage ; nohup python3 arbitrage_plot.py config.json 1>./log_arbitrage.log 2>&1 &
```