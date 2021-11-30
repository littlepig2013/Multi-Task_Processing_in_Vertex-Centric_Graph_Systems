#!/bin/bash

slaves=()



for slave in "${slaves[@]}"
do
	ssh $slave 'cd /root/vc-systems/GraphD/examples/basic_graphD_ppr/iopregel_localspace/ ; rm -rf ;'
done

