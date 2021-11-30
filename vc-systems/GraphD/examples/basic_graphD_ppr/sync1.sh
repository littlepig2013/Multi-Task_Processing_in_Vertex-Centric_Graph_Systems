#!/bin/bash

slaves=()
dir="~/vc-systems/"

type=$1
if [ "$type" = "1" ];then
	for slave in "${slaves[@]}"
	do
		scp -r "../basic_graphD_ppr/"  $slave":${dir}/GraphD/examples/"
	done
elif [ "$type" = "4" ];then
	for slave in "${slaves[@]}"
	do
		scp -r ${dir}/GraphD/system/* $slave":${dir}/GraphD/system/"
		scp "run"  $slave":${dir}/GraphD/examples/basic_graphD_ppr/"
		scp *.h  $slave":${dir}/GraphD/examples/basic_graphD_ppr/"
		scp *.cpp  $slave":${dir}/GraphD/examples/basic_graphD_ppr/"
		scp clean.sh  $slave":${dir}/GraphD/examples/basic_graphD_ppr/"
	done
elif [ "$type" = "3" ];then
	for slave in "${slaves[@]}"
	do
		scp -r "test_tmp_conf"  $slave":${dir}/GraphD/examples/basic_graphD_ppr"
	done
elif [ "$type" = "2" ];then
	for slave in "${slaves[@]}"
	do
		scp "batchedRWs.txt" $slave":${dir}/GraphD/examples/basic_graphD_ppr/"
	done
elif [ "$type" = "5" ];then
	for slave in "${slaves[@]}"
	do
		scp -r "../../../../GraphD/" $slave":${dir}/"
	done
	

fi


