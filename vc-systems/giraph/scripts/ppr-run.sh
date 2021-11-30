
#!/bin/bash

workload=6400
numworker="27"
batches=("1" "2" "4" "8" "16")
#workloads=("8")
#numworkers=("1")
dataset="dblp"
mkdir -p ppr_${dataset}_sync_exp/workers_${numworker}/
for batch in ${batches[@]}
do
		rworkload=`echo ${workload}/${batch} | bc`
		echo "Running workload ${workload} with #batches=${batch}"
		batchedStr="${rworkload}"
		for x in `seq 2 ${batch}`
		do
			batchedStr="${rworkload} ${batchedStr}"
		done
		echo ${batchedStr}	
		$HADOOP_HOME/bin/hadoop dfs -rmr /giraph_${dataset}_output/
		#DEBUG MODE
		#$HADOOP_HOME/bin/hadoop jar ~/giraph/giraph-examples/target/giraph-examples-1.3.0-SNAPSHOT-for-hadoop-1.2.1-jar-with-dependencies.jar org.apache.giraph.GiraphRunner org.apache.giraph.examples.PersonalizedPageRankComputationNaive -vif org.apache.giraph.examples.io.formats.JsonPPRVertexInputFormat -vip /giraph_${dataset}/ -vof org.apache.giraph.io.formats.IdWithValueTextOutputFormat -op /giraph_${dataset}_output/ -w ${numworker} -wc org.apache.giraph.examples.PersonalizedPageRankComputationNaiveWorkerContext -ca PersonalizedPageRankComputationNaive.PPRBatchedWalks="${batchedStr} ${rworkload}",PersonalizedPageRankComputationNaive.PPRBatchedWalksFlag=true,giraph.logLevel=debug 2>&1 | tee ppr_${dataset}_sync_exp/workers_${numworker}/workload_${workload}_b${batch}.txt 
		$HADOOP_HOME/bin/hadoop jar ~/giraph/giraph-examples/target/giraph-examples-1.3.0-SNAPSHOT-for-hadoop-1.2.1-jar-with-dependencies.jar org.apache.giraph.GiraphRunner org.apache.giraph.examples.PersonalizedPageRankComputationNaive -vif org.apache.giraph.examples.io.formats.JsonPPRVertexInputFormat -vip /giraph_${dataset}/ -vof org.apache.giraph.io.formats.IdWithValueTextOutputFormat -op /giraph_${dataset}_output/ -w ${numworker} -wc org.apache.giraph.examples.PersonalizedPageRankComputationNaiveWorkerContext -ca PersonalizedPageRankComputationNaive.PPRBatchedWalks="${batchedStr} ${rworkload}",PersonalizedPageRankComputationNaive.PPRBatchedWalksFlag=true 2>&1 | tee ppr_${dataset}_sync_exp/workers_${numworker}/workload_${workload}_b${batch}.txt 
done


