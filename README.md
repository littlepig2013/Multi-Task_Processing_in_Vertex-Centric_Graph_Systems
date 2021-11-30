The system codeswe use in our experiments are credited to [GraphD](http://www.cse.cuhk.edu.hk/systems/graphd/), [Pregel+](http://www.cse.cuhk.edu.hk/pregelplus/), [Giraph](giraph.apache.org), [Graphlab](https://github.com/jegonzal/PowerGraph).

You can refer to the above links to know the detailed instructions on setting up environment and running a program.

Codes we added or modified:

- PregelPlus: exmaples/*
- GraphD: examples/*
- Giraph: giraph-examples/src/main/java/org/apache/giraph/examples/PersonalizedPageRankComputation.java, giraph-examples/src/main/java/org/apache/giraph/examples/PersonalizedPageRankComputationWorkerContext.java, giraph-examples/src/main/java/org/apache/giraph/examples/io/PPRVertexValue.java
- Graphlab: CMakeLists.txt, toolkits/graph_analytics/personalized_pagerank.cpp, toolkits/graph_analytics/CMakeLists.txt

Other packages:
- gcc (6.3.0)
- mpich (3.2.1)
- boost (1_53_0)
- hadoop (1.2.1)
- openjdk (1.8.0_222)



