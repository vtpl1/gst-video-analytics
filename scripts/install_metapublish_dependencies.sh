#!/bin/bash
# ==============================================================================
# Copyright (C) 2018-2019 Intel Corporation
#
# SPDX-License-Identifier: MIT
# ==============================================================================

CURDIR=$PWD
cd /tmp/

apt update && apt install -y --no-install-recommends \
    uuid uuid-dev

wget -O - https://github.com/eclipse/paho.mqtt.c/archive/v1.3.1.tar.gz | tar -xz
cd paho.mqtt.c-1.3.1
make
make install
cd ..
rm -rf paho.mqtt.c-1.3.1

wget -O - https://github.com/edenhill/librdkafka/archive/v1.1.0.tar.gz | tar -xz
cd librdkafka-1.1.0
./configure --prefix=/usr --libdir=/usr/lib/x86_64-linux-gnu/
make
make install
cd ..
rm -rf librdkafka-1.1.0

wget -O - https://pocoproject.org/releases/poco-1.10.1/poco-1.10.1-all.tar.gz | tar -xz
cd poco-1.10.1-all
cmake . -DCMAKE_BUILD_TYPE=Release -DCMAKE_POSITION_INDEPENDENT_CODE=TRUE -DPOCO_STATIC=ON -DENABLE_DATA_MYSQL=OFF -DENABLE_TESTS=OFF -DENABLE_CRYPTO=ON -DENABLE_PAGECOMPILER=OFF -DENABLE_NETSSL=ON -DENABLE_PAGECOMPILER_FILE2PAGE=OFF -DPOCO_MT=OFF
cmake --build . --config Release j 8
make install
cd ..
rm -rf poco-1.10.1-all


cd $CURDIR
