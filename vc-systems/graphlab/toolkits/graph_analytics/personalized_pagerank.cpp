/*
 * Copyright (c) 2009 Carnegie Mellon University.
 *     All rights reserved.
 *
 *  Licensed under the Apache License, Version 2.0 (the "License");
 *  you may not use this file except in compliance with the License.
 *  You may obtain a copy of the License at
 *
 *      http://www.apache.org/licenses/LICENSE-2.0
 *
 *  Unless required by applicable law or agreed to in writing,
 *  software distributed under the License is distributed on an "AS
 *  IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either
 *  express or implied.  See the License for the specific language
 *  governing permissions and limitations under the License.
 *
 * For more about this software visit:
 *
 *      http://www.graphlab.ml.cmu.edu
 *
 */
#include <utility>
#include <map>
#include <set>
#include <string>
#include <ctime>
#include <fstream>
#include <iostream>
#include <stdlib.h>
#include <functional>

#include <graphlab.hpp>
#include <graphlab/serialization/vector.hpp>
#include <graphlab/graph/graph_basic_types.hpp>
#include <graphlab/graph/local_graph.hpp>
#include <graphlab/macros_def.hpp>
#include <boost/range/iterator_range.hpp>

// Global random reset probability
double RESET_PROB = 0.2;


size_t ITERATIONS = 0;

bool USE_DELTA_CACHE = false;

size_t numRWs = 32;

namespace std{
    std::ostream & operator<<(std::ostream & os, const std::vector<size_t> & v){
	for(auto item : v){
	    os << item << " ";
	}
	return os;
    }
}



std::vector<size_t> g_batchedRWs;
std::vector<int> g_fencePPR;
size_t g_numBatches;
double unitPPR = 1.0/32.0;



struct vertex_data_type {
   std::map<uint64_t, double>* ppr;
   std::vector<uint64_t>* out_neighbors;
   //std::vector<std::vector<std::pair<uint64_t, std::pair<uint64_t, size_t>>>>* agg_back_msgs;
   //std::vector<uint32_t>* agg_in_msgs;
   //std::vector<uint32_t>* agg_out_msgs;

  int batchNo;
  bool lastBatchFinished;
  bool output;
  int aggPPR;
   vertex_data_type(){
      output=false;
      //agg_in_msgs = new std::vector<uint32_t> (g_numBatches, 0);
      //agg_out_msgs = new std::vector<uint32_t> (g_numBatches, 0);
      ppr = new std::map<uint64_t, double> ();
      //neighbors = new std::vector<uint64_t> ();
      out_neighbors = new std::vector<uint64_t> ();

      batchNo = -1;
      lastBatchFinished = false;
      aggPPR = 0;
   }
   ~vertex_data_type(){
       ppr->clear();
       //delete ppr;
       //out_neighbors->clear();
       //delete out_neighbors;
   }

   void save(graphlab::oarchive& oarc) const {
      oarc << batchNo << lastBatchFinished << aggPPR;
      oarc << out_neighbors->size();
      for(size_t i = 0; i < out_neighbors->size(); i++){
          oarc << out_neighbors->at(i);
      }

      
      oarc << ppr->size();
      for(auto it = ppr->begin(); it != ppr->end(); it++){
          oarc << it->first << it->second;
      }
      /*
      for(int i = 0; i < g_numBatches; i++){
          oarc << agg_in_msgs->at(i) << agg_out_msgs->at(i);
      }*/
  
   }


   void load(graphlab::iarchive& iarc) {
      
      iarc >> batchNo >> lastBatchFinished >> aggPPR;
      size_t size = 0;
       iarc >> size;
      out_neighbors = new std::vector<uint64_t> (size, 0);
      for(size_t i = 0; i < size; i++){
         iarc >> out_neighbors->at(i);;
      }
      
      ppr = new std::map<uint64_t, double>();
      iarc >> size;
      uint64_t dst;
      double dst_ppr;
       for(size_t i = 0; i < size; i++){
          iarc >> dst >> dst_ppr;
          ppr->emplace(dst, dst_ppr); 
       }
     /*  
      agg_in_msgs = new std::vector<uint32_t> (g_numBatches, 0);
      agg_out_msgs = new std::vector<uint32_t> (g_numBatches, 0);
      for(int i = 0; i < g_numBatches; i++){
          iarc >> agg_in_msgs->at(i) >> agg_out_msgs->at(i);
      }*/
   }
};

//struct pagerank_message : public graphlab::IS_POD_TYPE {
struct pagerank_message {
    std::map<uint64_t, size_t> next_msgs;
    std::map<uint64_t, size_t> back_msgs;
    pagerank_message(){
       next_msgs = std::map<uint64_t, size_t> ();
       back_msgs = std::map<uint64_t, size_t> ();
    }
    pagerank_message(uint64_t src, size_t num_back_rws){
       next_msgs = std::map<uint64_t, size_t> ();
       back_msgs = std::map<uint64_t, size_t> ();
       back_msgs[src] = num_back_rws;
    }
    pagerank_message(std::map<uint64_t, size_t> & other){
       next_msgs = other;
       back_msgs = std::map<uint64_t, size_t> ();
    }
    ~pagerank_message(){
       next_msgs.clear();
       back_msgs.clear();
    }
    void save(graphlab::oarchive& oarc) const {
        oarc << next_msgs.size();
        for(auto it = next_msgs.begin(); it != next_msgs.end(); it++){
            oarc << it->first << it->second;
        }
        
        oarc << back_msgs.size();
        for(auto it = back_msgs.begin(); it != back_msgs.end(); it++){
            oarc << it->first << it->second;
        }
    }

    void load(graphlab::iarchive& iarc) {
      next_msgs = std::map<uint64_t, size_t>();
      back_msgs = std::map<uint64_t, size_t>();
      size_t size;
      uint64_t id;
      size_t counter;
      iarc >> size;
       for(size_t i = 0; i < size; i++){
          iarc >> id >> counter;
          next_msgs[id] = counter;
       }
      iarc >> size;
       for(size_t i = 0; i < size; i++){
          iarc >> id >> counter;
          back_msgs[id] = counter;
       }
   }


    pagerank_message & operator += (const pagerank_message & other){
        for(std::map<uint64_t, size_t>::const_iterator iter = other.next_msgs.begin(); iter != other.next_msgs.end(); iter++){
            if(next_msgs.find(iter->first) != next_msgs.end()){
               next_msgs[iter->first] = next_msgs[iter->first] + iter->second;
            }else{
               next_msgs[iter->first] = iter->second;
            }
        }
        for(std::map<uint64_t, size_t>::const_iterator iter = other.back_msgs.begin(); iter != other.back_msgs.end(); iter++){
            if(back_msgs.find(iter->first) != back_msgs.end()){
               back_msgs[iter->first] = back_msgs[iter->first] + iter->second;
            }else{
               back_msgs[iter->first] = iter->second;
            }
        }
        return *this;
    }

    double priority() const{
       return 1.0;
       //return next_msgs->size() + back_msgs->size();
    }

};

struct edge_data_type{
  //std::set<uint64_t>* out_neighbors = NULL;
  //std::set<uint64_t>* in_neighbors = NULL;
  //map<uint64_t, std::pair<std::vector<uint64_t>, size_t>> msg2; // target to source
  //map<uint64_t, std::pair<std::vector<uint64_t>, size_t>> back_msg2;
   std::vector<uint64_t> out_neighbors;
  edge_data_type() { 
    out_neighbors = std::vector<uint64_t> ();
   //msg = new std::map<uint64_t, std::pair<std::vector<uint64_t>, size_t> > (); 
   //back_msg = new std::map<uint64_t, std::pair<std::vector<uint64_t>, size_t> > ();
   //  source -> path, #rw 
   //  dst -> path, #rw
   //msg2 = map<uint64_t, std::pair<std::vector<uint64_t>, size_t>> ();
   //out_neighbors = new std::set<uint64_t>();
   //in_neighbors = new std::set<uint64_t>();
   //back_msg2 = map<uint64_t, std::pair<std::vector<uint64_t>, size_t>> ();
  }
 
  
  edge_data_type & operator += (const edge_data_type & other){
         for(int i = 0; i < other.out_neighbors.size(); i++){
              out_neighbors.push_back(other.out_neighbors[i]);
         }
        //dc.cout() << out_neighbors << " --- " << in_neighbors << std:endl;
        //dc.cout() << other.out_neighbors << " --- " << other.in_neighbors << std:endl;
       /*
       if(other.out_neighbors->size()){
           for(std::set<uint64_t>::const_iterator iter = other.out_neighbors->begin(); iter != other.out_neighbors->end(); iter++){
               out_neighbors->insert(*iter); 
           } 
       }

       if(other.in_neighbors->size()){
           for(std::set<uint64_t>::const_iterator iter = other.in_neighbors->begin(); iter != other.in_neighbors->end(); iter++){
               in_neighbors->insert(*iter); 
           } 
       }
	*/

    
       return *this;
  }
  void save(graphlab::oarchive& oarc) const {
       oarc << out_neighbors.size();
      for(size_t i = 0; i < out_neighbors.size(); i++){
          oarc << out_neighbors[i];
      }
   }
   void load(graphlab::iarchive& iarc) {
      
      size_t size = 0;
       iarc >> size;
      out_neighbors = std::vector<uint64_t> (size, 0);
      for(size_t i = 0; i < size; i++){
         iarc >> out_neighbors[i];
      }
      
          
   }
};


// The graph type is determined by the vertex and edge data types
typedef graphlab::distributed_graph<vertex_data_type, edge_data_type> graph_type;

/**
 * \brief Get the other vertex in the edge.
 */
inline graph_type::vertex_type
get_other_vertex(const graph_type::edge_type& edge,
                 const graph_type::vertex_type& vertex) {
  return vertex.id() == edge.source().id()? edge.target() : edge.source();
}


/*
 * A simple function used by graph.transform_vertices(init_vertex);
 * to initialize the vertes data.
 */
void init_vertex(graph_type::vertex_type& vertex) { 
   vertex.data() = vertex_data_type(); 
}



/*
 * The factorized page rank update function extends ivertex_program
 * specifying the:
 *
 *   1) graph_type
 *   2) gather_type: double (returned by the gather function). Note
 *      that the gather type is not strictly needed here since it is
 *      assumed to be the same as the vertex_data_type unless
 *      otherwise specified
 *
 * In addition ivertex program also takes a message type which is
 * assumed to be empty. Since we do not need messages no message type
 * is provided.
 *
 * personalized_pagerank also extends graphlab::IS_POD_TYPE (is plain old data type)
 * which tells graphlab that the personalized_pagerank program can be serialized
 * (converted to a byte stream) by directly reading its in memory
 * representation.  If a vertex program does not exted
 * graphlab::IS_POD_TYPE it must implement load and save functions.
 */
class personalized_pagerank :
  public graphlab::ivertex_program<graph_type, edge_data_type, pagerank_message> {

public:
  std::map<uint64_t, size_t> r_next_msgs;
  std::map<uint64_t, size_t> r_back_msgs;
  
  void init(icontext_type& context, const vertex_type& vertex, pagerank_message msg){
     r_next_msgs = msg.next_msgs;
     r_back_msgs = msg.back_msgs;
  }  
  /**
   * Gather only in edges.
   */
  edge_dir_type gather_edges(icontext_type& context,
                              const vertex_type& vertex) const {
    
    if(vertex.data().batchNo == -1 && !vertex.data().lastBatchFinished){
    return graphlab::OUT_EDGES;
    }else{
    return graphlab::NO_EDGES;

    }
  } // end of Gather edges


  /* Gather the weighted rank of the adjacent page   */
  edge_data_type gather(icontext_type& context, const vertex_type& vertex,
               edge_type& edge) const {
     
    if(vertex.data().batchNo == -1 && !vertex.data().lastBatchFinished){
       edge.data().out_neighbors.push_back(edge.target().id());
       /*
       if(edge.target().id() != vertex.id() && edge.source().id() == vertex.id()){
           vertex.data().out_neighbors->push_back((uint64_t)edge.target().id());
       }else if(edge.target().id() == vertex.id() && edge.source().id() != vertex.id()){
           edge.target().data().out_neighbors->push_back((uint64_t) vertex.id());
       }*/
    }
/*
    if(vertex.data().lastBatchFinished){

       dc.cout() << "Not Gathering " << vertex.data().batchNo << std::endl;
    }
   */ 
    return edge.data();
  }

  /* Use the total rank of adjacent pages to update this page */
  void apply(icontext_type& context, vertex_type& vertex,
             const gather_type& total) {
       uint64_t id = vertex.id();
    if(!vertex.data().lastBatchFinished && vertex.data().batchNo == -1){
        for(size_t i = 0 ; i < total.out_neighbors.size(); i++){
            vertex.data().out_neighbors->push_back(total.out_neighbors[i]);
        }
    }
    size_t out_degree = vertex.num_out_edges();
    if(vertex.data().lastBatchFinished){

       if(vertex.data().batchNo < (int)g_numBatches){ 
          vertex.data().batchNo = vertex.data().batchNo + 1;
       }
    }
    if(vertex.data().batchNo == -1 || vertex.data().batchNo >= (int) g_numBatches){
       vertex.data().lastBatchFinished = true;
       //if(!vertex.data().output && r_back_msgs.size() == 0 && r_next_msgs.size() == 0 && vertex.data().batchNo >= (int) g_numBatches){
       /*
       dc.cout() << "Batched in-messages:";
       for(int i = 0; i < (int) g_numBatches; i++){
           dc.cout() << "\t" << vertex.data().agg_in_msgs->at(i);
       }
       dc.cout() << std::endl;*/
       /*
       dc.cout() << "Batched out-messages:";
       for(int i = 0; i < (int) g_numBatches; i++){
           dc.cout() << "\t" << vertex.data().agg_out_msgs->at(i);
       }
       dc.cout() << std::endl;*/
       //   vertex.data().output = true;
       //}
    }
    std::vector<size_t>* split_msgs = NULL; 
    std::vector<std::map<uint64_t, size_t>>* agg_msgs = new std::vector<std::map<uint64_t, size_t>>(out_degree, std::map<uint64_t, size_t>() );
    std::map<uint64_t, size_t>* agg_back_msgs = new std::map<uint64_t, size_t> ();

    if(vertex.data().batchNo >= 0 && vertex.data().batchNo <(int) g_numBatches && vertex.data().lastBatchFinished){
       vertex.data().lastBatchFinished = false; 
        

      if(out_degree == 0){
          vertex.data().ppr->emplace(id, 1.0);
          vertex.data().lastBatchFinished = true;
      }else{
      split_msgs = new std::vector<size_t> (out_degree, 0);
      size_t num_back_msgs = 0;
      for(size_t i = 0; i < g_batchedRWs[vertex.data().batchNo]; i++){
          double p = (double) rand() / (RAND_MAX);
          if(p > RESET_PROB){
             split_msgs->at(rand() %  out_degree)++;
          }else{
             num_back_msgs++;
          }
      } 
     //dc.cout() << "vertex debugging: " << vertex.id() << "-" << vertex.data().batchNo << "-" << vertex.data().lastBatchFinished << "-" << num_back_msgs << std::endl;
      if(num_back_msgs > 0){
      if(vertex.data().ppr->find(id) == vertex.data().ppr->end()){
          vertex.data().ppr->emplace(id, unitPPR*num_back_msgs);
      }else{
          vertex.data().ppr->at(id) = vertex.data().ppr->at(id) + unitPPR*num_back_msgs;
      }
      //dc.cout() <<"current ppr: " << id << " : " << vertex.data().ppr->at(id) << std::endl;
      vertex.data().aggPPR += num_back_msgs;
      }
      for(size_t i = 0; i < out_degree; i++){
          if(split_msgs->at(i) == 0) continue;
          agg_msgs->at(i)[id] = split_msgs->at(i);
      }
      delete split_msgs;
     
       }
    }
   
    bool isBatchNoValid = vertex.data().batchNo >= 0 && vertex.data().batchNo < (int) g_numBatches;
    /*
    if(isBatchNoValid){
        if(r_next_msgs.size() > 0 || r_back_msgs.size() > 0)
            vertex.data().agg_in_msgs->at(vertex.data().batchNo) += 1;
    }*/
    auto iter = r_next_msgs.begin();
    while(iter != r_next_msgs.end()){
        
        size_t num_back_msgs = 0;
        size_t num_rws = iter->second;
        if(out_degree > 0){
        split_msgs = new std::vector<size_t> (out_degree, 0);
        for(size_t i = 0; i < num_rws; i++){
            double p = (double) rand()*1.0/RAND_MAX;
            if(p > RESET_PROB){
               split_msgs->at(rand()%out_degree)++;
            }else{
               num_back_msgs++;
            }
        }
      
        for(size_t i = 0; i < out_degree; i++){ 
            if(split_msgs->at(i) == 0) continue;
            if(agg_msgs->at(i).find(iter->first) == agg_msgs->at(i).end()){
                agg_msgs->at(i).emplace(iter->first, split_msgs->at(i));
            }else{
                agg_msgs->at(i)[iter->first] = agg_msgs->at(i)[iter->first] + split_msgs->at(i);
            }
            
        }
        delete split_msgs;
       }else{
          num_back_msgs = num_rws;
       }
        if(num_back_msgs > 0){
            if(agg_back_msgs->find(iter->first) == agg_back_msgs->end()){
                agg_back_msgs->emplace(iter->first, num_back_msgs);
            }else{
                size_t old_num_rws = agg_back_msgs->at(iter->first);
                agg_back_msgs->at(iter->first) =  num_back_msgs + old_num_rws;
            }
        }
        iter++;
    }
    r_next_msgs.clear();


    std::map<uint64_t, double>* ppr = vertex.data().ppr;
    auto iter_back = r_back_msgs.begin();
    while(iter_back != r_back_msgs.end()){
          uint64_t vid = iter_back->first;
          double old_value = 0.0;
           if(ppr->find(vid) != ppr->end()){
              old_value = ppr->at(vid); 
           } else{
              ppr->emplace(vid, 0.0);
           }
           double new_value = old_value + iter_back->second*unitPPR;
           vertex.data().ppr->at(vid) = new_value;
           //dc.cout() << "vertex id: " << vertex.id() << " dest: " << vid << " old (" << old_value << " ) -> new (" << new_value << "==" << vertex.data().ppr->at(vid) << ")" << std::endl;
           vertex.data().aggPPR += iter_back->second;
        
       iter_back++;
    }
    r_back_msgs.clear();
    
     

	//dc.cout() << vertex.data().batchNo << "\t" << g_numBatches << std::endl;

     if(agg_back_msgs->size() > 0 ){
	 //dc.cout() << id << "\t" << agg_back_msgs->size() << std::endl;
         for(auto iter = agg_back_msgs->begin(); iter != agg_back_msgs->end(); iter++){
             context.signal_vid(iter->first, pagerank_message(id, iter->second));
         }
     }
     agg_back_msgs->clear();
     delete agg_back_msgs;

    
     for(size_t i = 0; i < agg_msgs->size(); i++){
  
        if(agg_msgs->at(i).size() > 0){
           context.signal_vid(vertex.data().out_neighbors->at(i), pagerank_message(agg_msgs->at(i)));
           agg_msgs->at(i).clear();
	   /*
           if(isBatchNoValid)
               vertex.data().agg_out_msgs->at(vertex.data().batchNo)++;
	    */
        }
     }
     //dc.cout() << "Applying " << std::endl; 
     agg_msgs->clear();
     delete agg_msgs;
    

     if(isBatchNoValid){
           // if(rand()*1.0/RAND_MAX < 0.2)
           //dc.cout() << "testing " << id << "\t" << vertex.data().aggPPR << "\t" <<  g_fencePPR[vertex.data().batchNo]<< std::endl;
       if(g_fencePPR[vertex.data().batchNo] <= vertex.data().aggPPR){
          vertex.data().lastBatchFinished = true;
       }else{
          vertex.data().lastBatchFinished = false;
      }
       //vertex.data().agg_out_msgs->at(vertex.data().batchNo) += agg_back_msgs->size();
    }

    
     if(vertex.data().lastBatchFinished && vertex.data().batchNo < (int) g_numBatches){
         context.signal(vertex);
     }
  }

  /* The scatter edges depend on whether the personalized_pagerank has converged */
  edge_dir_type scatter_edges(icontext_type& context,
                              const vertex_type& vertex) const {

   
      return graphlab::NO_EDGES;
  }

  /* The scatter function just signal adjacent pages */
  void scatter(icontext_type& context, const vertex_type& vertex,
               edge_type& edge) const {
      return;    
  
  }
  void save(graphlab::oarchive& oarc) const {
    oarc << r_next_msgs.size();
    for(auto it = r_next_msgs.begin(); it != r_next_msgs.end(); it++){
      oarc << it->first << it->second;
    }
    oarc << r_back_msgs.size();
    for(auto it = r_back_msgs.begin(); it != r_back_msgs.end(); it++){
      oarc << it->first << it->second;
    }
  }



  void load(graphlab::iarchive& iarc) {
     size_t size = 0;
     r_next_msgs = std::map<uint64_t, size_t> ();
     r_back_msgs = std::map<uint64_t, size_t> ();
     uint64_t tmp_vid;
     size_t tmp_num_rws;
     iarc >> size;
     for(size_t i = 0; i < size; i++){
        iarc >> tmp_vid >> tmp_num_rws;
        r_next_msgs[tmp_vid] = tmp_num_rws;
     }
     
     iarc >> size;
     for(size_t i = 0; i < size; i++){
        iarc >> tmp_vid >> tmp_num_rws;
        r_back_msgs[tmp_vid] = tmp_num_rws;
     }
  }

}; // end of factorized_personalized_pagerank update functor


/*
 * We want to save the final graph so we define a write which will be
 * used in graph.save("path/prefix", personalized_pagerank_writer()) to save the graph.
 */
struct personalized_pagerank_writer {
  std::string save_vertex(graph_type::vertex_type v) {
    std::stringstream strm;
    strm << v.id() << "\t";
    std::map<uint64_t, double>* r = v.data().ppr;
    for(auto iter = r->begin(); iter != r->end(); iter++){
	strm << iter->first << ":" << iter->second << "; ";
    }
    strm << "\n";
    return strm.str();
  }
  std::string save_edge(graph_type::edge_type e) { return ""; }
}; // end of personalized_pagerank writer





int main(int argc, char** argv) {
  // Initialize control plain using mpi
  graphlab::mpi_tools::init(argc, argv);
  
  global_logger().set_log_level(LOG_INFO);

  graphlab::distributed_control dc;
  // Parse command line options -----------------------------------------------
  graphlab::command_line_options clopts("PersonalizedPageRank algorithm.");
  std::string graph_dir;
  std::string format = "adj";
  std::string exec_type = "synchronous";
  clopts.attach_option("graph", graph_dir,
                       "The graph file.  If none is provided "
                       "then a toy graph will be created");
  clopts.add_positional("graph");
  clopts.attach_option("engine", exec_type,
                       "The engine type synchronous or asynchronous");
  clopts.attach_option("format", format,
                       "The graph file format");
  clopts.attach_option("batchedRWs", g_batchedRWs,
                       "batched random walks. ");
  clopts.add_positional("batchedRWs");
  
  std::string saveprefix;
  clopts.attach_option("saveprefix", saveprefix,
                       "If set, will save the resultant personalized_pagerank to a "
                       "sequence of files with prefix saveprefix");

  if(!clopts.parse(argc, argv)) {
    dc.cout() << "Error in parsing command line arguments." << std::endl;
    return EXIT_FAILURE;
  }
  numRWs = 0;
  g_numBatches = g_batchedRWs.size();
  //dc.cout() << "#num batches: " << g_numBatches << std::endl;
  std::cout << "#num batches: " << g_numBatches << std::endl;
  for(size_t i = 0; i < g_numBatches; i++){
     numRWs += g_batchedRWs[i];
  }
  
  unitPPR = 1.0/numRWs;
  g_fencePPR = std::vector<int>(g_numBatches, 0);
  g_fencePPR[0] = g_batchedRWs[0];
  //dc.cout() << g_fencePPR[0];
  std::cout << g_fencePPR[0];
  for(size_t i = 1; i < g_numBatches; i++){
     g_fencePPR[i] = g_fencePPR[i-1] + g_batchedRWs[i];
     //dc.cout() << "\t" << g_fencePPR[i];
     std::cout << "\t" << g_fencePPR[i];
  }
  //dc.cout() << std::endl;
  std::cout << std::endl;

  // Enable gather caching in the engine


  size_t powerlaw = 0;
  clopts.attach_option("powerlaw", powerlaw,
                       "Generate a synthetic powerlaw out-degree graph. ");
  // Build the graph ----------------------------------------------------------
  graph_type graph(dc, clopts);
  if(powerlaw > 0) { // make a synthetic graph
    dc.cout() << "Loading synthetic Powerlaw graph." << std::endl;
    graph.load_synthetic_powerlaw(powerlaw, false, 2.1, 100000000);
  }
  else if (graph_dir.length() > 0) { // Load the graph from a file
    dc.cout() << "Loading graph in format: "<< format << std::endl;
    graph.load_format(graph_dir, format);
  }
  else {
    dc.cout() << "graph or powerlaw option must be specified" << std::endl;
    clopts.print_description();
    return 0;
  }
  // must call finalize before querying the graph
  graph.finalize();
  dc.cout() << "#vertices: " << graph.num_vertices()
            << " #edges:" << graph.num_edges() << std::endl;

  // Initialize the vertex data
  graph.transform_vertices(init_vertex);

  // Running The Engine -------------------------------------------------------
  graphlab::omni_engine<personalized_pagerank> engine(dc, graph, exec_type, clopts);
  engine.signal_all();
  engine.start();
  const double runtime = engine.elapsed_seconds();
  dc.cout() << "Finished Running engine in " << runtime
            << " seconds." << std::endl;



  // Save the final graph -----------------------------------------------------
  if (saveprefix != "") {
    graph.save(saveprefix, personalized_pagerank_writer(),
               false,    // do not gzip
               true,     // save vertices
               false);   // do not save edges
  }


  // Tear-down communication layer and quit -----------------------------------
  graphlab::mpi_tools::finalize();
  return EXIT_SUCCESS;
} // End of main


// We render this entire program in the documentation


