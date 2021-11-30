#!/bin/bash
slaves=()
dir="~/vc-systems/"
type=$1
if [ "$type" = "1" ];then
	for slave in "${slaves[@]}"
	do
		scp -r "../basic_pregelplus_sssp"  $slave":"$dir"/PregelPlus/examples/"
	done
elif [ "$type" = "2" ];then
	for slave in "${slaves[@]}"
	do
		scp "batchedSeeds.txt"  $slave":"$dir"/PregelPlus/examples/basic_pregelplus_sssp/"
	done
elif [ "$type" = "3" ];then
	for slave in "${slaves[@]}"
	do
		scp "test_tmp_conf"  $slave":"$dir"/PregelPlus/examples/basic_pregelplus_sssp/"
	done
elif [ "$type" = "4" ];then
	for slave in "${slaves[@]}"
	do
		scp "run"  $slave":"$dir"/PregelPlus/examples/basic_pregelplus_sssp/"
		scp *.h  $slave":"$dir"/PregelPlus/examples/basic_pregelplus_sssp/"
		scp *.cpp  $slave":"$dir"/PregelPlus/examples/basic_pregelplus_sssp/"
	done
fi


