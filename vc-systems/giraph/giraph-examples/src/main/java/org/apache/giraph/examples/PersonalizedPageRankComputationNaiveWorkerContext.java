package org.apache.giraph.examples;

import org.apache.giraph.utils.MemoryUtils;
import org.apache.giraph.worker.WorkerContext;
import org.apache.log4j.Logger;


public class PersonalizedPageRankComputationNaiveWorkerContext extends WorkerContext {

    private static final Logger LOG = Logger.getLogger(PersonalizedPageRankComputationNaiveWorkerContext.class);
    private double teleportationProbability = 0.20; 
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
	Long numVertexes = getTotalNumVertices();
	long superstep = getSuperstep();
	Long stepLimit = (long)(Math.log(numVertexes)/teleportationProbability) + 1;
	/*
        if(LOG.isDebugEnabled()){
            LOG.debug("Memory Info before GC:" + MemoryUtils.getRuntimeMemoryStats() + "*******************\t\t\n\n\n");
            System.gc();
            LOG.debug("Memory Info after GC:" + MemoryUtils.getRuntimeMemoryStats() + "*******************\t\t\n\n\n");
        }*/
	int currentBatchInnerStep = (int)(superstep%(stepLimit+2));
	System.out.println("Worker Count = " + getWorkerCount() + " *******************\t\t\n\n\n");
        System.out.println("Memory Info before GC:" + superstep + ":" + MemoryUtils.getRuntimeMemoryStats() + "*******************\t\t\n\n\n");
	if(currentBatchInnerStep == 0){
            System.gc();
            System.out.println("Memory Info after GC:" + superstep+":"+MemoryUtils.getRuntimeMemoryStats() + "*******************\t\t\n\n\n");
	}
    }
}
