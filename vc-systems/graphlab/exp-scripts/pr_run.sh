#!/bin/bash

confpath="/root/vc-systems/graphlab/tmp_conf"
executablepath="/root/vc-systems/graphlab/release/toolkits/graph_analytics/pagerank"
hdfspath="hdfs://localhost:54312/"
dataset="dblp"
inputpath="${dataset}_pregelplus/"
outputpath="${dataset}_graphlab_output/"
tol="0.01"

#numworkers=("1" "2" "4" "8" "16" "27")
numworkers=("16" "27")
for numworker in ${numworkers[@]}
do
	head -${numworker} /root/vc-systems/PregelPlus/examples/basic_pregelplus_ppr/tmp_conf > ${confpath}
	mpiexec -n ${numworker} -f ${confpath} ${executablepath} --engine synchronous --graph ${hdfspath}${inputpath} --saveprefix ${hdfspath}${outputpath} --ncpus 1 --tol ${tol} 2>&1 | tee pagerank_exp/${dataset}_sync_${numworker}.txt
	mpiexec -n ${numworker} -f ${confpath} ${executablepath} --engine asynchronous --graph ${hdfspath}${inputpath} --saveprefix ${hdfspath}${outputpath} --ncpus 1 --tol ${tol} 2>&1 | tee pagerank_exp/${dataset}_async_${numworker}.txt
done
