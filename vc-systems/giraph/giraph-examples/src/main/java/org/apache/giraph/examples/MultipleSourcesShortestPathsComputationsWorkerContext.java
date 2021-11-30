package org.apache.giraph.examples;

import org.apache.giraph.utils.MemoryUtils;
import org.apache.giraph.worker.WorkerContext;
import org.apache.hadoop.io.BooleanWritable;

public class MultipleSourcesShortestPathsComputationsWorkerContext extends WorkerContext {
    private static final String LAST_BATCHED_FINISHED_AGG = "L";
    @Override
    public void preApplication() throws InstantiationException, IllegalAccessException {

    }

    @Override
    public void postApplication() {

    }

    @Override
    public void preSuperstep() {

    }

    @Override
    public void postSuperstep() {
        long superstep = getSuperstep();
        System.out.println("Worker Count = " + getWorkerCount() + " *******************\t\t\n\n\n");
        System.out.println("Memory Info before GC:" + superstep + ":" + MemoryUtils.getRuntimeMemoryStats() + "*******************\t\t\n\n\n");
        if(((BooleanWritable)getAggregatedValue(LAST_BATCHED_FINISHED_AGG)).get()){
            System.gc();
            System.out.println("Memory Info after GC:" + superstep+":"+MemoryUtils.getRuntimeMemoryStats() + "*******************\t\t\n\n\n");
        }

    }
}

