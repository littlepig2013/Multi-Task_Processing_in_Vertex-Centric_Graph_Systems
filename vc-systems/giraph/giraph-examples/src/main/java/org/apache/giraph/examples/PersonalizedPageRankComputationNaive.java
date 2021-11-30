package org.apache.giraph.examples;

import org.apache.giraph.conf.BooleanConfOption;
import org.apache.giraph.conf.IntConfOption;
import org.apache.giraph.conf.JsonStringConfOption;
import org.apache.giraph.examples.io.PPRBaselineMessageWritable;
import org.apache.giraph.graph.BasicComputation;
import org.apache.giraph.edge.Edge;
import org.apache.giraph.graph.Vertex;
import org.apache.hadoop.io.FloatWritable;
import org.apache.hadoop.io.LongWritable;
import org.apache.log4j.Logger;
import org.apache.giraph.examples.io.PPRVertexValue;
import org.json.JSONArray;

import java.io.IOException;
import java.util.*;


@Algorithm(name = "Personalized PageRanks", description = "Compute Personalized PageRanks")
public class PersonalizedPageRankComputationNaive
        extends BasicComputation<LongWritable, PPRVertexValue, FloatWritable, PPRBaselineMessageWritable> {

    /** Class logger */
    private static final Logger LOG = Logger.getLogger(PersonalizedPageRankComputationNaive.class);

    private static boolean adaptiveWalkFlag = false;
    private static boolean testWalkFlag = false;
    private static boolean PPRBatchedWalksFlag = false;
    private static long defaultTestTotalNumRWs = 1024l;
    private static int testBatch = 1;
    private double teleportationProbability = 0.20;

    private static final BooleanConfOption adaptiveWalkFlagConfOption =
            new BooleanConfOption("PersonalizedPageRankComputationNaive.adaptiveWalkFlag",
                    adaptiveWalkFlag, "the adaptive walk flag in PPR Naive Computation");
    private static final BooleanConfOption testWalkFlagConfOption =
            new BooleanConfOption("PersonalizedPageRankComputationNaive.testWalkFlag",
                    testWalkFlag, "the test walk flag in PPR Naive Computation");
    private static final IntConfOption testWalkBatchOption =
            new IntConfOption("PersonalizedPageRankComputationNaive.testBatch",
                   testBatch, "the batch number for testing in PPR Naive Computation");
    private static final BooleanConfOption PPRBatchedWalksFlagConfOption =
            new BooleanConfOption("PersonalizedPageRankComputationNaive.PPRBatchedWalksFlag",
                    PPRBatchedWalksFlag, "the flag of batched walks in PPR Naive Computation");
    private static final JsonStringConfOption PPRBatchedWalksConfOption =
            new JsonStringConfOption("PersonalizedPageRankComputationNaive.PPRBatchedWalks",
                    "batched walks in PPR Naive Computation");


    @Override
    public void compute(Vertex<LongWritable, PPRVertexValue, FloatWritable> vertex, Iterable<PPRBaselineMessageWritable> messages)
            throws IOException{

        Long numVertexes = getTotalNumVertices();
        Long numRWs = Math.round(Math.log(numVertexes));

        long superstep = getSuperstep();

        Long currentVertexId = vertex.getId().get();
        int numNeighbors = vertex.getNumEdges();
        List<Edge<LongWritable, FloatWritable>> listEdges = new ArrayList<>();
        for (Edge<LongWritable, FloatWritable> edge : vertex.getEdges()) {
            listEdges.add(edge);
        }
        Random randomGenerator = new Random();
        Map<Long, Double> vertexValueHash = vertex.getValue().get(); 
        Long stepLimit = (long)(Math.log(numVertexes)/teleportationProbability) + 1;

        int currentBatch = (int)(superstep/(stepLimit+2));

        double unitPPR = 1.0/numRWs;
        if(adaptiveWalkFlagConfOption.get(getConf())){
            numRWs *= listEdges.size();
            unitPPR /= listEdges.size();
        }else if(testWalkFlagConfOption.get(getConf())){
            testBatch = testWalkBatchOption.get(getConf());
            unitPPR = 1.0/defaultTestTotalNumRWs;
            numRWs = defaultTestTotalNumRWs/testBatch;
        }else if(PPRBatchedWalksFlagConfOption.get(getConf())){
            if(LOG.isDebugEnabled())
            LOG.debug("RW Batch Info:" + PPRBatchedWalksConfOption.getRaw(getConf()) + " *********** \t\t\n\n");
            String batchedWalksStr = PPRBatchedWalksConfOption.getRaw(getConf());
            String[] batchedWalksStrArray = batchedWalksStr.split(" ");
            testBatch = batchedWalksStrArray.length - 1;
            numRWs = Long.parseLong(batchedWalksStrArray[currentBatch]);
            unitPPR = 1.0/Long.parseLong(batchedWalksStrArray[testBatch]);
        }

        int currentBatchInnerStep = (int)(superstep%(stepLimit+2));
        if (currentBatchInnerStep == 0 && currentBatch < testBatch) {
            if(LOG.isDebugEnabled())
            LOG.debug("PPR starts with " + testBatch + " batch(es) + and " + stepLimit + " limited steps per walk *******************\t\t\n\n\n");

            vertexValueHash.put(currentVertexId, 0.0);
            ArrayList<Integer> nextNeighborIds = new ArrayList<>();
            for(long i = 0; i < numRWs; i++){
                if(randomGenerator.nextDouble() <= teleportationProbability){
                    double currentPPR = vertexValueHash.get(currentVertexId);
                    currentPPR += unitPPR;
                    vertexValueHash.put(currentVertexId, currentPPR);
                }else{
                    int index = randomGenerator.nextInt(numNeighbors);
                    nextNeighborIds.add(index);
                }
            }

            double currentPPR = vertexValueHash.get(currentVertexId);
            if(currentPPR == 0.0){
                vertexValueHash.remove(currentVertexId);
            }

            vertex.setValue(new PPRVertexValue(vertexValueHash));

            int  size = nextNeighborIds.size();
            for(int i = 0; i < size; i++){
                Edge<LongWritable, FloatWritable> edge = listEdges.get(nextNeighborIds.get(i));
                LongWritable targetVertexId = edge.getTargetVertexId();
                sendNaivePPRMessage(currentVertexId, targetVertexId.get(), false);
            }

            if(LOG.isDebugEnabled()) LOG.debug("super step "+currentVertexId +":"+vertexValueHash.get(currentVertexId)+"*******************\t\t\n\n\n");


        } else if (currentBatchInnerStep < stepLimit && currentBatch < testBatch) {

            if(LOG.isDebugEnabled()) LOG.debug("super step "+superstep+"*******************\t\t\n\n\n");

            for (PPRBaselineMessageWritable message : messages) {
                Boolean backFlag = message.getBackFlag();
                if(backFlag == true){ // collect PPR
                    getUpdatedVertexValueHash(message.getSourceId(), vertexValueHash, unitPPR);
                }else{ // stopFlag = false

                    if(randomGenerator.nextDouble() <= teleportationProbability || numNeighbors == 0){
                        sendNaivePPRMessage(currentVertexId, message.getSourceId(), true);
                    }else{
                        int index = randomGenerator.nextInt(numNeighbors);
                        Edge<LongWritable, FloatWritable> edge = listEdges.get(index);
                        if(index>=listEdges.size()){
                            throw new IOException("index >= listEdges size");
                        }
                        sendNaivePPRMessage(message.getSourceId(), edge.getTargetVertexId().get(), false);
                    }
                }
            }

            vertex.setValue(new PPRVertexValue(vertexValueHash));

        } else if (currentBatchInnerStep == stepLimit && currentBatch < testBatch ) {
            for (PPRBaselineMessageWritable message : messages) {

                Boolean stopFlag = message.getBackFlag();
                if(stopFlag == true){ // collect PPR
                    getUpdatedVertexValueHash(message.getSourceId(), vertexValueHash, unitPPR);
                }else{
                    sendNaivePPRMessage(currentVertexId, message.getSourceId(), true);
                }
            }

            vertex.setValue(new PPRVertexValue(vertexValueHash));

        } else if (currentBatchInnerStep == stepLimit + 1l && currentBatch < testBatch ) {

            for (PPRBaselineMessageWritable message: messages) {
                getUpdatedVertexValueHash(message.getSourceId(), vertexValueHash, unitPPR);
            }

            vertex.setValue(new PPRVertexValue(vertexValueHash));
        } else if (currentBatch >= testBatch){
            vertex.voteToHalt();
        }

    }

    private void getUpdatedVertexValueHash(Long vertexId, Map<Long, Double> vertexValueHash, double unitPPR){
        if(vertexValueHash.containsKey(vertexId)){
            double currentPPR = vertexValueHash.get(vertexId);
            currentPPR += unitPPR;
            vertexValueHash.put(vertexId, currentPPR);
        }else{
            vertexValueHash.put(vertexId, unitPPR);
        }
    }

    private void sendNaivePPRMessage(Long sourceId, Long targetId, Boolean backFlag){
        LongWritable targetIdLongWritable = new LongWritable(targetId);
        PPRBaselineMessageWritable newPPRFinishedMessage = new PPRBaselineMessageWritable(sourceId, targetId, backFlag);
        sendMessage(targetIdLongWritable, newPPRFinishedMessage);
    }

}
