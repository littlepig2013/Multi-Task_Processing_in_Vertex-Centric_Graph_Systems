/*
 * Licensed to the Apache Software Foundation (ASF) under one
 * or more contributor license agreements.  See the NOTICE file
 * distributed with this work for additional information
 * regarding copyright ownership.  The ASF licenses this file
 * to you under the Apache License, Version 2.0 (the
 * "License"); you may not use this file except in compliance
 * with the License.  You may obtain a copy of the License at
 *
 *     http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

package org.apache.giraph.examples;

import org.apache.giraph.graph.BasicComputation;
import org.apache.giraph.edge.Edge;
import org.apache.giraph.graph.Vertex;
import org.apache.hadoop.io.FloatWritable;
import org.apache.hadoop.io.LongWritable;
import org.apache.log4j.Logger;
import org.apache.giraph.examples.io.PPRMessageWritable;
import org.apache.giraph.examples.io.PPRVertexValue;

import java.io.IOException;
import java.util.*;

/**
 * Demonstrates the basic Pregel shortest paths implementation.
 */
@Algorithm(name = "Personalized PageRanks", description = "Compute Personalized PageRanks")
public class PersonalizedPageRankComputation
    extends BasicComputation<LongWritable, PPRVertexValue, FloatWritable, PPRMessageWritable> {

  /** The shortest paths id */
  // public static final LongConfOption SOURCE_ID =
  //     new LongConfOption("SimpleShortestPathsVertex.sourceId", 1,
  //         "The shortest paths id");
  /** Class logger */
  private static final Logger LOG = Logger.getLogger(PersonalizedPageRankComputation.class);

  // /**
  //  * Is this vertex the source id?
  //  *
  //  * @param vertex Vertex
  //  * @return True if the source id
  //  */
  // private boolean isSource(Vertex<LongWritable, ?, ?> vertex) {
  //   return vertex.getId().get() == SOURCE_ID.get(getConf());
  // }

  // @Override
  // public void compute(
  //     Vertex<LongWritable, DoubleWritable, FloatWritable> vertex,
  //     Iterable<DoubleWritable> messages) throws IOException {
  //   if (getSuperstep() == 0) {
  //     vertex.setValue(new DoubleWritable(Double.MAX_VALUE));
  //   }
  //   double minDist = isSource(vertex) ? 0d : Double.MAX_VALUE;
  //   for (DoubleWritable message : messages) {
  //     minDist = Math.min(minDist, message.get());
  //   }
  //   if (LOG.isDebugEnabled()) {
  //     LOG.debug("Vertex " + vertex.getId() + " got minDist = " + minDist +
  //         " vertex value = " + vertex.getValue());
  //   }
  //   if (minDist < vertex.getValue().get()) {
  //     vertex.setValue(new DoubleWritable(minDist));
  //     for (Edge<LongWritable, FloatWritable> edge : vertex.getEdges()) {
  //       double distance = minDist + edge.getValue().get();
  //       if (LOG.isDebugEnabled()) {
  //         LOG.debug("Vertex " + vertex.getId() + " sent to " +
  //             edge.getTargetVertexId() + " = " + distance);
  //       }
  //       sendMessage(edge.getTargetVertexId(), new DoubleWritable(distance));
  //     }
  //   }
  //   vertex.voteToHalt();
  // }

  @Override
  public void compute(Vertex<LongWritable, PPRVertexValue, FloatWritable> vertex, Iterable<PPRMessageWritable> messages)
      throws IOException {
    long superstep = getSuperstep();
    Long numRWs = 64l;
    long log_steps = Math.round(Math.log(numRWs));
    Random randomGenerator = new Random();
    if (superstep == 0) {

      int numNeighbors = vertex.getNumEdges();
      List<Edge<LongWritable, FloatWritable>> listEdges = new ArrayList<Edge<LongWritable, FloatWritable>>();
      for (Edge<LongWritable, FloatWritable> edge : vertex.getEdges()) {
        listEdges.add(edge);
      }
      for (int i = 1; i <= numRWs; i++) {

        int index = randomGenerator.nextInt(numNeighbors);
        Edge<LongWritable, FloatWritable> edge = listEdges.get(index);
        if(i<=(numRWs+1)/2.0){
        sendMessage(edge.getTargetVertexId(),
            new PPRMessageWritable(vertex.getId().get(), edge.getTargetVertexId().get(), 1l, Long.valueOf(i)));
        }
        // if (vertex.getId().get()!=edge.getTargetVertexId().get()) {
        if(i>=(numRWs+1)/2.0){
          sendMessage(vertex.getId(),
          new PPRMessageWritable(vertex.getId().get(), edge.getTargetVertexId().get(), 1l, Long.valueOf(i)));
        }
        // }

      }
      // LOG.debug("superstep = 0 finished!\n");

    } 
    else if (superstep <= log_steps) {
      if(LOG.isDebugEnabled())
        LOG.debug("superstep = "+superstep+"\n");
      Long sumRWs = Math.round(1.0+numRWs / Math.pow(2.0, superstep - 1.0));
      if(LOG.isDebugEnabled())
        LOG.debug("sumRWs: "+sumRWs+"\n");
      Map<Long, Long> sourceMaps = new HashMap<Long, Long>();
      Long vertexId = Long.valueOf(vertex.getId().get());
      for (PPRMessageWritable message : messages) {
        Long sid = message.getSourceId();
        Long tid = message.getTargetId();
        Long rwId = message.getRandomWalkId();
        if (sid.equals(vertexId)) {
          sourceMaps.put(rwId, tid);
        }

      }
      
      for (PPRMessageWritable message : messages) {
        Long sid = message.getSourceId();
        Long tid = message.getTargetId();

        Long p = message.getPropagate();
        Long rwId = message.getRandomWalkId();
        if (tid.equals(vertexId)) {

          Long rwId2 = sumRWs - rwId;
          if (rwId2 >= rwId) {
            if (!sourceMaps.containsKey(rwId2)) {
              throw new IOException(
                  "sumRWs: " + sumRWs + " superstep: " + superstep + " sourceMaps not contain key " + rwId2 + "\n");
            }
            if (LOG.isDebugEnabled())
              LOG.debug("ids " + rwId + " " + rwId2 + "\n");
            Long tid2 = sourceMaps.get(rwId2);
            // Long newRWid = Math.min(rwId, rwId2);
            // new PPRMessageWritable(vertexId, tid2, 1l, newRWid);
            // new PPRMessageWritable(vertexId, tid2, 1l, newRWid);
            if(superstep<log_steps){
              if(rwId>=(sumRWs)/4.0){
                sendMessage(new LongWritable(sid), new PPRMessageWritable(sid, tid2, p, rwId));
              }
              // if (!sid.equals(tid2)) {
              if(rwId<=(sumRWs)/4.0){
                sendMessage(new LongWritable(tid2), new PPRMessageWritable(sid, tid2, p, rwId));
              }
            }
            else if(superstep==log_steps){
              sendMessage(new LongWritable(sid), new PPRMessageWritable(sid, tid2, p, rwId));

            }
            // }
          }
        }

      }
      // LOG.info("superstep "+superstep+" finished!\n");
    }

    else if (superstep == Math.round(Math.log(numRWs))+1l) {
      if(LOG.isDebugEnabled())
        LOG.info("superstep "+superstep+"\n");
      Map<Long, Double> vertexValueHash = new HashMap<Long, Double>();
      Long vertexId = Long.valueOf(vertex.getId().get());
      for (PPRMessageWritable message : messages) {
        
        Long sid = message.getSourceId();
        Long tid = message.getTargetId();

        if (sid.equals(vertexId)) {
          vertexValueHash.put(tid, 1.0);
          // throw new IOException("vertexId "+vertexId);
        }
        // throw new IOException("has message!");

      }
      PPRVertexValue vertexValue=new PPRVertexValue(vertexValueHash);
      vertex.setValue(vertexValue);
      if(LOG.isDebugEnabled())
        LOG.info("superstep "+superstep+" finished!\n");
    }

    vertex.voteToHalt();
  }

}
