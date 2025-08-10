#!/usr/bin/bash


sudo docker run -d --privileged -v `pwd`:/project -p 80:80 -p 81:81 -p 82:82 thundertrader/develstudio:1.81
