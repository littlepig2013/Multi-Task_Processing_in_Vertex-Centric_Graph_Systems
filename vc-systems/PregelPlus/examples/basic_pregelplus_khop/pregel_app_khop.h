#include "basic/pregel-dev.h"
#include "malloc.h"
#include <map>
#include <cmath>
#include <ctime>
#include <iostream>
#include <fstream>
#include <string>

#include <unistd.h>
#include <sys/types.h>

using namespace std;

#define E 0.0001
#define EPSILON 1
#define MAX_ITERATION 16

int logSwitch;
int pid = 0;
int testBatch;
int k = 2;
int maxWorkload;
vector<set<int> > batchedSeeds;
vector<int> batchedWorkload;

string get_memory_info(string s){
	string result = "";
	if(pid == 0){
		cout << "Invliad pid: " << pid << endl;
	}else{
		stringstream ss;
		ss << pid;
		string pidFileName = "/proc/" + ss.str() + "/status";
		ifstream procInfoIn(pidFileName.c_str(), ios::in);		
		string line;
		while(getline(procInfoIn, line)){
			if(line.rfind(s, 0) == 0){
				result = line;
				break;
			}
		}
		procInfoIn.close();
	}
	return result;
}

//input line format: vertexID \t numOfNeighbors neighbor1 neighbor2 ...
//output line format: v \t v1:KHop1 v2:KHop2 ...

struct KHopValue_pregel
{
	vector<VertexID> edges;
	map<int, int> khop_nodes;
};

ibinstream & operator<<(ibinstream & m, const KHopValue_pregel & v){;
	m<<v.edges;
	m<<v.khop_nodes;
	return m;
}

obinstream & operator>>(obinstream & m, KHopValue_pregel & v){
	m>>v.edges;
	m>>v.khop_nodes;
	return m;
}

struct KHopMsg_pregel
{
	//VertexID source;
	//map<int, double> values;
	map<VertexID, int> sources;
};

ibinstream & operator<<(ibinstream & m, const KHopMsg_pregel & v){
	//m<<v.source;
	m<<v.sources;
	return m;
}

obinstream & operator>>(obinstream & m, KHopMsg_pregel & v){
	//m>>v.source;
	m>>v.sources;
	return m;
}


struct KHopAggType {
	int currentBatch;
	int iteration;
	map<int, double> dev;
	bool startFlag;
	int msgNum;
	KHopAggType (){
		currentBatch = 0;
		iteration = 0;
		startFlag = true;
		msgNum = 0;
	}
};

ibinstream & operator<<(ibinstream & m, const KHopAggType & v) {
	m << v.currentBatch;
	m << v.iteration;
	m << v.dev;
	m << v.startFlag;
	m << v.msgNum;
	return m;
}

obinstream & operator>>(obinstream & m, KHopAggType & v) {
	m >> v.currentBatch;
	m >> v.iteration;
	m >> v.dev;
	m >> v.startFlag;
	m >> v.msgNum;
	return m;
}



//====================================

class KHopVertex_pregel:public Vertex<VertexID, KHopValue_pregel, KHopMsg_pregel>
{
	const double teleportationProbability = 0.20;

	public:
		map<int, double> dev;
		int msgNum;

		virtual void compute(MessageContainer & messages)
		{

			msgNum = 0;
			int superstep = step_num() - 1;
			int numVertexes = get_vnum();
			
			//KHopAggType* agg = (KHopAggType*) getAgg();
			//bool startFlag = agg->startFlag;
			//int currentBatch = agg->currentBatch;
			int currentBatch = superstep/(k+1);
			if(currentBatch >= testBatch){
				vote_to_halt();
			}else{
				int innerSuperstep = superstep%(k+1);
				int degree = value().edges.size();
				if(innerSuperstep == 0){
					if(batchedSeeds[currentBatch].find(id) != batchedSeeds[currentBatch].end()){
						if(k == 0){
							value().khop_nodes[id] = 1;
							vote_to_halt();
						}else{
							KHopMsg_pregel	msg;
							msg.sources[id] = 1;

							for(int d = 0; d < degree; d++){
								send_message(value().edges[d], msg);
							}
							msgNum += degree;
							msg.sources.clear();
						}
												
					}
				}else if(innerSuperstep < k - 1){
					map<VertexID, int> sources;
					for(int i = 0; i < messages.size(); i++){
						for(map<VertexID, int>::iterator iter = messages[i].sources.begin(); iter != messages[i].sources.end(); iter++){
							VertexID node = iter->first;
							if(sources.find(node) == sources.end()){
								sources[node] = 0;
							}
							sources[node] += iter->second;
						}
						messages[i].sources.clear();
					}
					KHopMsg_pregel msg;
					msg.sources = sources;
					for(int  d = 0; d < degree; d++){
						send_message(value().edges[d], msg);
					}		
					msgNum += degree;
					sources.clear();
				}else if(innerSuperstep == k - 1){
					KHopMsg_pregel msg;
					for(int d = 0; d < degree; d++){
						msg.sources[value().edges[d]] = 1;
					}
					for(int i = 0; i < messages.size(); i++){
						for(map<VertexID, int>::iterator iter = messages[i].sources.begin(); iter != messages[i].sources.end(); iter++){
							KHopMsg_pregel tmp_msg = msg;
							for(map<VertexID, int>::iterator s_iter = tmp_msg.sources.begin(); s_iter != tmp_msg.sources.end(); s_iter++){
								s_iter->second *= iter->second;
							}
							send_message(iter->first, tmp_msg);	
							msgNum++;
						}
						messages[i].sources.clear();
					}
					msg.sources.clear();	
				}else if(innerSuperstep == k){
					map<int, int> khop_nodes;
					for(int i = 0; i < messages.size(); i++){
						for(map<VertexID, int>::iterator iter = messages[i].sources.begin(); iter != messages[i].sources.end(); iter++){
							VertexID node = iter->first;
							if(khop_nodes.find(node) == khop_nodes.end()){
								khop_nodes[node] = 0;
							}
							khop_nodes[node] += iter->second;
						}
						messages[i].sources.clear();
					}
					value().khop_nodes = khop_nodes;
					khop_nodes.clear();

				}
			}
			
		}
};

class KHopAgg: public Aggregator<KHopVertex_pregel, KHopAggType,KHopAggType> {
private:
	KHopAggType	value;
public:
	virtual void init() {
		value.msgNum = 0;
		value = *((KHopAggType*) getAgg());
	}

	virtual void stepPartial(KHopVertex_pregel * v){
		value.msgNum += v->msgNum;
	}

	virtual void stepFinal(KHopAggType* p){
		value.msgNum += p->msgNum;
	}

	virtual KHopAggType* finishPartial(){
		
		if(logSwitch == 1){
			string s1="VmHWM";
			string s2="VmRSS";
			cout << _my_rank << " sent " << value.msgNum << " messages in this superstep" << endl;
			stringstream ss;
			ss << _my_rank;	
			cout << "\n" + ss.str() + " " + get_memory_info(s1) << endl;
			cout << "\n" + ss.str() + " " + get_memory_info(s2) << endl;
		}
		/*
		for(map<int, double>::iterator iter = value.dev.begin(); iter != value.dev.end(); iter++){
			cout << "Error: " << iter->first << " " << iter->second << endl;
		}*/
		return &value;
	}

	virtual KHopAggType* finishFinal(){
		return &value;		
	}

};


class KHopWorker_pregel:public Worker<KHopVertex_pregel, KHopAgg>
{
	char buf[400];

	public:
		//C version
		virtual KHopVertex_pregel* toVertex(char* line)
		{
			char * pch;
			pch=strtok(line, "\t");
			KHopVertex_pregel* v=new KHopVertex_pregel;
			v->id=atoi(pch);
			pch=strtok(NULL, " ");
			int num=atoi(pch);
			for(int i=0; i<num; i++)
			{
				pch=strtok(NULL, " ");
				v->value().edges.push_back(atoi(pch));
			}
			return v;
		}

		virtual void toline(KHopVertex_pregel* v, BufferedWriter & writer)
		{
			sprintf(buf, "%d\t", v->id); 
			writer.write(buf);
			for(map<int, int>::iterator iter = v->value().khop_nodes.begin(); iter != v->value().khop_nodes.end(); iter++){
				char tmpBuf[50];
				sprintf(tmpBuf, " %d:%d", iter->first, iter->second);
				writer.write(tmpBuf);
			}
			
			writer.write("\n");
		}
};

//void pregel_khop(vector<int> _batchedWorkload, string in_path, string out_path, int _logSwitch = 0)
//void pregel_ppr(string in_path, string out_path, int _testBatch, int _numWorkloads, int _logSwitch = 0)
void pregel_khop(vector<set<int> > _batchedSeeds, string in_path, string out_path,int _k, int _logSwitch = 0)
{
	//numWorkloads = _numWorkloads;
	//unitKHop = 1.0/numWorkloads;
	//unitKHop = 1.0/128;
	//testBatch = _testBatch;
	k = _k;
	cout << "k: " << k << endl;
	batchedSeeds = _batchedSeeds;
	testBatch = _batchedSeeds.size();
	cout << "Test Batch: " << testBatch << endl;
	logSwitch = _logSwitch;
	if(logSwitch == 1){
		pid = (int) getpid();
		cout << "Worker " << get_worker_id() << " starts logging..." << endl;
		cout << "Worker pid: " << pid << endl;
	}
	WorkerParams param;
	param.input_path=in_path;
	param.output_path=out_path;
	param.force_write=true;
	param.native_dispatcher=false;
	KHopWorker_pregel worker;
	KHopAgg agg;
	worker.setAggregator(&agg);
	worker.run(param);
}

