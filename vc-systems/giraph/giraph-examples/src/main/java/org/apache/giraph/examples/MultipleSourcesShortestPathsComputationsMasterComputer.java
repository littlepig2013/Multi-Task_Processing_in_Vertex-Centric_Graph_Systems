package org.apache.giraph.examples;

import org.apache.giraph.aggregators.BooleanAndAggregator;
import org.apache.giraph.aggregators.BooleanOverwriteAggregator;
import org.apache.giraph.aggregators.IntOverwriteAggregator;
import org.apache.giraph.aggregators.IntSumAggregator;
import org.apache.giraph.master.DefaultMasterCompute;
import org.apache.hadoop.io.BooleanWritable;
import org.apache.hadoop.io.DoubleWritable;
import org.apache.hadoop.io.IntWritable;

public class MultipleSourcesShortestPathsComputationsMasterComputer
        extends DefaultMasterCompute {

    private static final String LAST_BATCHED_FINISHED_AGG = "L";
    private static final String CURRENT_BATCHED_FINISHED_AGG = "C";
    private static final String BATCH_NUMBER_AGG = "b";
    //private static final String MESSAGES_AGG = "m";
    @Override
    public void compute(){
	System.out.println("Superstep xx " + getSuperstep() + "\n");
        boolean last_batch_finished_flag = ((BooleanWritable)getAggregatedValue(CURRENT_BATCHED_FINISHED_AGG)).get();
        //boolean last_batch_finished_flag = ((BooleanWritable)getAggregatedValue(LAST_BATCHED_FINISHED_AGG)).get();
	System.out.println("Superstep " + getSuperstep() + " : " +  last_batch_finished_flag + "\n");
       
        if(last_batch_finished_flag){
            int batchNo = ((IntWritable) getAggregatedValue(BATCH_NUMBER_AGG)).get();
            setAggregatedValue(BATCH_NUMBER_AGG,new IntWritable(batchNo+1));
        }
        setAggregatedValue(LAST_BATCHED_FINISHED_AGG, new BooleanWritable(last_batch_finished_flag));
        setAggregatedValue(CURRENT_BATCHED_FINISHED_AGG, new BooleanWritable(true));
    }

    @Override
    public void initialize() throws InstantiationException, IllegalAccessException {
        super.initialize();
        //registerAggregator(MESSAGES_AGG, IntSumAggregator.class);
        registerPersistentAggregator(CURRENT_BATCHED_FINISHED_AGG, BooleanAndAggregator.class);
        registerPersistentAggregator(LAST_BATCHED_FINISHED_AGG, BooleanOverwriteAggregator.class);
        //registerAggregator(LAST_BATCHED_FINISHED_AGG, BooleanAndAggregator.class);
        registerPersistentAggregator(BATCH_NUMBER_AGG, IntOverwriteAggregator.class);
        setAggregatedValue(LAST_BATCHED_FINISHED_AGG, new BooleanWritable(true));
        setAggregatedValue(CURRENT_BATCHED_FINISHED_AGG, new BooleanWritable(true));
        setAggregatedValue(BATCH_NUMBER_AGG, new IntWritable(0));
        //setAggregatedValue(MESSAGES_AGG, new IntWritable(0));
    }
}

