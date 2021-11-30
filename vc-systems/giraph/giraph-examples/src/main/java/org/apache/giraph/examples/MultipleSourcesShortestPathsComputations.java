package org.apache.giraph.examples;

import org.apache.giraph.conf.BooleanConfOption;
import org.apache.giraph.conf.IntConfOption;
import org.apache.giraph.conf.JsonStringConfOption;
import org.apache.giraph.examples.io.MSSPMessageWritable;
import org.apache.giraph.examples.io.PPRBaselineMessageWritable;
import org.apache.giraph.graph.BasicComputation;
import org.apache.giraph.edge.Edge;
import org.apache.giraph.graph.Vertex;
import org.apache.hadoop.io.*;
import org.apache.log4j.Logger;
import org.apache.giraph.examples.io.MSSPVertexValue;
import org.json.JSONArray;

import java.io.IOException;
import java.util.HashMap;
import java.util.ArrayList;
import java.util.LinkedList;
import java.util.HashSet;
import java.util.Map;

@Algorithm(name = "Multi-Source Shortest Paths", description = "Compute MSSP")
public class MultipleSourcesShortestPathsComputations
        extends BasicComputation<LongWritable, MSSPVertexValue, FloatWritable, MSSPMessageWritable> {

    /**
     * Class logger
     */
    private static final Logger LOG = Logger.getLogger(MultipleSourcesShortestPathsComputations.class);


    private static final JsonStringConfOption MSSPTotalSeedsConfOption =
            new JsonStringConfOption("MultipleSourcesShortestPathsComputations.MSSPTotalSeeds",
                    "total seeds in MSSP Computation");
    private static final JsonStringConfOption MSSPBatchedSeedsConfOption =
            new JsonStringConfOption("MultipleSourcesShortestPathsComputations.MSSPBatchedSeeds",
                    "batched seeds in MSSP Computation");

    private static final String LAST_BATCHED_FINISHED_AGG = "L";
    private static final String CURRENT_BATCHED_FINISHED_AGG = "C";
    private static final String BATCH_NUMBER_AGG = "b";
    //private static final String MESSAGES_AGG = "m";
    @Override
    public void compute(Vertex<LongWritable, MSSPVertexValue, FloatWritable> vertex, Iterable<MSSPMessageWritable> messages)
            throws IOException {

	LinkedList<Integer> batchedSeeds = new LinkedList();
	if(MSSPBatchedSeedsConfOption.contains(getConf())){
                //LOG.debug("Batched Seeds: " + MSSPBatchedSeedsConfOption.getRaw(getConf()) + " ******* \t\t\n\n");
                System.out.println("Batched Seeds: " + MSSPBatchedSeedsConfOption.getRaw(getConf()) + " ******* \t\t\n\n");
                String[] tmpbatchedSeeds = MSSPBatchedSeedsConfOption.getRaw(getConf()).split(" ");
		for(int i = 0; i < tmpbatchedSeeds.length; i++){
			batchedSeeds.add(Integer.parseInt(tmpbatchedSeeds[i]));
		}
	}
        int numBatches = batchedSeeds.size() - 1;
	if(numBatches < 0){
		numBatches = 1;
	}
        boolean batch_finished_flag = ((BooleanWritable) getAggregatedValue(LAST_BATCHED_FINISHED_AGG)).get();
        int batchNo = ((IntWritable) getAggregatedValue(BATCH_NUMBER_AGG)).get();
	//int batchNo = vertex.getValue().getCurrentBatch();
        Map<Long, Double> vertexValueHash = vertex.getValue().getValues();
        boolean updated = false;
	
        System.out.println("batch finished:" + batch_finished_flag + "\t batch number: " + batchNo + " ******* \t\t\n\n");
        if (batch_finished_flag && batchNo <= numBatches) {
	    //vertex.getValue().incCurrentBatch();
            String[] totalSeeds = {"2"}; 
            if(MSSPTotalSeedsConfOption.contains(getConf())){
		if(LOG.isDebugEnabled()){
                	LOG.debug("Seeds: " + MSSPTotalSeedsConfOption.getRaw(getConf()) + " ******* \t\t\n\n");
                	System.out.println("Seeds: " + MSSPTotalSeedsConfOption.getRaw(getConf()) + " ******* \t\t\n\n");
		}
                totalSeeds = MSSPTotalSeedsConfOption.getRaw(getConf()).split(" ");
			
            }else{

                //LOG.warn("Seeds are not specified using 2 as the only source (batchSeeds is deprecated) ******* \t\t\n\n");
                System.out.println("Seeds are not specified using 2 as the only source (batchSeeds is deprecated) ******* \t\t\n\n");

            }
	    if(numBatches == 1){
               batchedSeeds = new LinkedList();
               batchedSeeds.add(totalSeeds.length);
            }

            //MSSPTotalSeedsConfOption.getRaw(getConf());
            int finishedSeeds = 0;
            for (int i = 1; i < batchNo; i++) {
                finishedSeeds += batchedSeeds.get(i-1);
            }
            int seedsNum = batchedSeeds.get(batchNo-1);
            HashSet<Long> seeds = new HashSet<Long>();
            for (int i = 0; i < seedsNum && i < totalSeeds.length - finishedSeeds; i++) {
		Long tmpVertexID = Long.parseLong(totalSeeds[i + finishedSeeds]);
                seeds.add(tmpVertexID);
		vertex.getValue().putNewMSSPValue(tmpVertexID, Double.MAX_VALUE);
            }
            Long vertexID = vertex.getId().get();
            if (seeds.contains(vertexID)) {
                vertex.getValue().putNewMSSPValue(vertexID, 0.0);
                aggregate(CURRENT_BATCHED_FINISHED_AGG, new BooleanWritable(false));
                //aggregate(LAST_BATCHED_FINISHED_AGG, new BooleanWritable(false));
            }else{
                aggregate(CURRENT_BATCHED_FINISHED_AGG, new BooleanWritable(true));
                //aggregate(LAST_BATCHED_FINISHED_AGG, new BooleanWritable(true));
            }

            for (Edge<LongWritable, FloatWritable> edge : vertex.getEdges()) {
                HashMap<Long, Double> msgValue = new HashMap<>();
                double distance = edge.getValue().get();
                msgValue.put(vertexID, distance);
                if (LOG.isDebugEnabled()) {
                    //LOG.debug("Vertex " + vertex.getId() + " sent to " +
                    //       edge.getTargetVertexId() + " = " + msgValue.toString());
                    System.out.println("Vertex " + vertex.getId() + " sent to " +
                            edge.getTargetVertexId() + " = " + msgValue.toString());
                }
                sendMessage(edge.getTargetVertexId(), new MSSPMessageWritable(msgValue));
            }
                //aggregate(MESSAGES_AGG, new IntWritable(vertex.getNumEdges()));



        } else if (!batch_finished_flag) {
            HashMap<Long, Double> min = new HashMap<>();
            for(MSSPMessageWritable message: messages){
                for(Map.Entry<Long, Double> entry:message.getValues().entrySet()){
                    Long sourceID = entry.getKey();
                    Double distance = entry.getValue();
                    if(!vertexValueHash.containsKey(sourceID) || vertexValueHash.get(sourceID) > distance) {
                        min.put(sourceID, distance);
			vertexValueHash.put(sourceID, distance);
                    }
                }
            }

            if(min.size() > 0){
		vertex.getValue().setValues(vertexValueHash);	
                for (Edge<LongWritable, FloatWritable> edge : vertex.getEdges()) {
                    HashMap<Long, Double> msgValue = new HashMap<>();
                    double distance = edge.getValue().get();
                    for(HashMap.Entry<Long,Double> entry:min.entrySet()){
                        msgValue.put(entry.getKey(),entry.getValue()+distance);
                    }
                    if (LOG.isDebugEnabled()) {
                        //LOG.debug("Vertex " + vertex.getId() + " sent to " +
                        //       edge.getTargetVertexId() + " = " + msgValue.toString());
                        System.out.println("Vertex " + vertex.getId() + " sent to " +
                                edge.getTargetVertexId() + " = " + msgValue.toString());
                    }
                    sendMessage(edge.getTargetVertexId(), new MSSPMessageWritable(msgValue));
		    msgValue.clear();
                }
		min.clear();
                //aggregate(MESSAGES_AGG, new IntWritable(vertex.getNumEdges()));
                aggregate(CURRENT_BATCHED_FINISHED_AGG, new BooleanWritable(false));
                //aggregate(LAST_BATCHED_FINISHED_AGG, new BooleanWritable(false));
            }else{
                aggregate(CURRENT_BATCHED_FINISHED_AGG, new BooleanWritable(true));
                //aggregate(LAST_BATCHED_FINISHED_AGG, new BooleanWritable(true));
            }


        } else {
            vertex.voteToHalt();
        }


    }
}

