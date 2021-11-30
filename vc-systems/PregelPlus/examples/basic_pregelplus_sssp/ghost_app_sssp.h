#include "basic/pregel-dev.h"
#include <unistd.h>
#include <float.h>
#include <fstream>
#include <algorithm>
#include <vector>
#include <map>
#include <set>

#include <ctime>
#include <unistd.h>
#include <sys/types.h>
using namespace std;

#define LOG_FILE_NAME "log.txt"

int logSwitch;
int pid = 0;

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

string readAggregates(){
	ifstream fin("aggregates.txt", ios::in);
	string line;
	stringstream ss;
	int line_idx = 0;
	while(getline(fin, line)){
		if(line_idx%2 == 0){
			ss << line << " ";
		}
		line_idx++;
	}
	fin.close();
	cout << ss.str() << endl;
	return ss.str();
}



//input line format: vertexID \t numOfNeighbors neighbor1 neighbor2 ...
//edge lengths are assumed to be 1

//output line format: v \t shortest_path_length  previous_vertex_on_shorest_path
//previous_vertex_on_shorest_path=-1 for source vertex
int batchNum = 0;
vector<set<int> > batchedSeeds;

//====================================

struct SPMsg{
	map<int, int> from_dist;
	SPMsg(map<int, int> _from_dist) :
		from_dist(_from_dist){
	}
	SPMsg(){
		from_dist = map<int, int>();
	}
};

ibinstream & operator<<(ibinstream & m, const SPMsg& v) {
	m << v.from_dist;
	return m;
}

obinstream & operator>>(obinstream & m, SPMsg & v) {
	m >> v.from_dist;
	return m;
}

struct SPValue {
	vector<VertexID> edges;
	//vector<double> edges_weight;
	//vector<int> froms;
	//vector<int> dists;
	map<int, int> from_dist;
		
};
ibinstream & operator<<(ibinstream & m, const SPValue & v){;
	m<<v.edges;
	//m<<v.froms;
	//m<<v.dists;
	//m<<v.edges_weight;
	m<<v.from_dist;
	return m;
}

obinstream & operator>>(obinstream & m, SPValue & v){
	m>>v.edges;
	//m>>v.froms;
	//m>>v.dists;
	//m>>v.edges_weight;
	m>>v.from_dist;
	return m;
}

struct SPAggType {
	int msgNum;
	bool isBatchFinished;
	int currentBatch;
	SPAggType (){
		isBatchFinished = true;
		currentBatch = 0;
		msgNum = 0;
	}
};

ibinstream & operator<<(ibinstream & m, const SPAggType & v) {
	m << v.isBatchFinished;
	m << v.currentBatch;
	m << v.msgNum;
	return m;
}

obinstream & operator>>(obinstream & m, SPAggType & v) {
	m >> v.isBatchFinished;
	m >> v.currentBatch; 
	m >> v.msgNum;
	return m;
}



class SPVertex_pregel: public Vertex<VertexID, SPValue, SPMsg> {
private:
	void broadcast_sssp_message(SPMsg msg, set<int> seeds){
		SPMsg t_msg;
		for(map<int, int>::iterator iter = msg.from_dist.begin(); iter != msg.from_dist.end(); iter++){
			if(seeds.find(iter->first) != seeds.end()){
				t_msg.from_dist[iter->first] = iter->second + 1;
			}
		}
		int neighborsNum = value().edges.size();
		for(int i = 0; i < neighborsNum; i++){
			send_message(value().edges[i], t_msg);
		}
		t_msg.from_dist.clear();
	}
public:
	bool isChanged;
	int msgNum;
	int currentBatch;
	virtual void compute(MessageContainer & messages) {
		isChanged = false;
		msgNum = 0;
		SPAggType* agg = (SPAggType*) getAgg();
		currentBatch = agg->currentBatch;
		if (agg->currentBatch < batchNum && agg->isBatchFinished) {
			isChanged = true;
			map<int, int> from_dist = value().from_dist;
			/*
			for(map<int, int>::iterator iter = from_dist.begin(); iter != from_dist.end(); iter++){
				value().froms.push_back(iter->first);
				value().froms.push_back(iter->second);
			}*/
			set<int> currentSeeds = batchedSeeds[agg->currentBatch];
			if(currentSeeds.find(id) != currentSeeds.end()){
				value().from_dist[id] = 0;
				broadcast_sssp_message(SPMsg(value().from_dist), currentSeeds);
				msgNum += value().edges.size();
			}
			currentSeeds.clear();
		} else if (!agg->isBatchFinished){
			set<int> currentSeeds = batchedSeeds[agg->currentBatch];
			SPMsg min;
			map<int, int> from_dist;
			for (int i = 0; i < messages.size(); i++) {
				SPMsg msg = messages[i];
				from_dist = msg.from_dist;
				for(map<int, int>::iterator iter = from_dist.begin(); iter != from_dist.end(); iter++){
					int from = iter->first;
					int dist = iter->second;
					if(value().from_dist.find(from) == value().from_dist.end() || value().from_dist[from] > dist){
						value().from_dist[from] = dist;
						min.from_dist[from] = dist;
						isChanged = true;
					}
				}
				from_dist.clear();	
				map<int, int> empty_map;
				from_dist.swap(empty_map);
			}
			if (isChanged) {
				broadcast_sssp_message(min, currentSeeds);
				msgNum += value().edges.size();
			}
			currentSeeds.clear();
		}else{
			/*
			map<int, int> from_dist = value().from_dist;
			for(map<int, int>::iterator iter = from_dist.begin(); iter != from_dist.end(); iter++){
				value().froms.push_back(iter->first);
				value().froms.push_back(iter->second);
			}
			from_dist.clear();
			map<int , int> empty_map;
			from_dist.swap(empty_map);
			value().from_dist.clear();
			*/

			vote_to_halt();
		}
	}

};

class SPAgg: public Aggregator<SPVertex_pregel, SPAggType, SPAggType> {

private:
	SPAggType value;
public:
	virtual void init() {
		value.isBatchFinished = true;
		value.msgNum = 0;
		value.currentBatch = INT_MAX;
	}

	virtual void stepPartial(SPVertex_pregel* v){
		value.currentBatch = min(v->currentBatch, value.currentBatch); 
		if(v->isChanged == true){
			value.isBatchFinished = false;
			value.msgNum += v->msgNum;
		}

	}

	virtual void stepFinal(SPAggType* p){
		if(p->isBatchFinished == false){
			value.isBatchFinished = false;
		}
		value.msgNum += p->msgNum;

	}

	virtual SPAggType* finishPartial(){
		if(logSwitch == 1 && value.currentBatch < batchedSeeds.size()){
			string s1 = "VmHWM";
			string s2 = "VmRSS";
			//cout << _my_rank << " sent " << value.msgNum << " messages in this superstep" << endl;
			
			ofstream fout ("mem-log.txt", ofstream::out|ofstream::app);
			stringstream ss;
			ss << _my_rank;	
			fout << value.currentBatch << " "  + ss.str() + " " + get_memory_info(s1) << endl;
			fout << value.currentBatch << " " + ss.str() + " " + get_memory_info(s2) << endl;
			fout.close();
		
		}
		return &value;
	}

	virtual SPAggType* finishFinal(){
		if(value.isBatchFinished && value.currentBatch < batchedSeeds.size()){
			time_t t = std::time(0);
			tm* now = std::localtime(&t);
			ofstream fout(LOG_FILE_NAME, ofstream::out| ofstream::app);
			system("python log_aggregator.py");
			fout << "[LOG] Batch " << value.currentBatch << " " << readAggregates() << " curr_time: " << now->tm_hour <<"-" << now->tm_min <<"-" << now->tm_sec << endl;
			fout.close();

			value.currentBatch += 1;
			cout << " Current Batch " << value.currentBatch << endl;
		}
		return &value;
	}
};

class SPWorker_pregel: public Worker<SPVertex_pregel, SPAgg> {
	char buf[100];
public:

	virtual SPVertex_pregel* toVertex(char* line) {
		char * pch;
		pch = strtok(line, "\t");
		SPVertex_pregel* v = new SPVertex_pregel;
		int id = atoi(pch);
		v->id = id;
		pch=strtok(NULL, " ");
		int num=atoi(pch);
		for(int i=0; i<num; i++)
		{
			pch=strtok(NULL, " ");
			v->value().edges.push_back(atoi(pch));
			//v->value().edges_weight.push_back(1.0);
		}
		return v;
	}

	virtual void toline(SPVertex_pregel* v, BufferedWriter & writer) {
		sprintf(buf, "%d\t", v->id);
		writer.write(buf);
		/*
		for(int i = 0; i < v->value().froms.size(); i++){
			char tmpBuf[50];
			sprintf(tmpBuf, " %d:%d ", v->value().froms[i], v->value().dists[i]);
			writer.write(tmpBuf);
		}
		*/
		map<int, int> from_dist = v->value().from_dist;
		for(int i = 0; i < batchNum; i++){
			set<int> seeds = batchedSeeds[i];
			for(set<int>::iterator iter=seeds.begin();iter != seeds.end(); iter++){
				int currentSeed = *iter;
				if(from_dist.find(currentSeed) != from_dist.end() && from_dist[currentSeed] != DBL_MAX){
					
					char tmpBuf[50];
					sprintf(tmpBuf, " %d:%d ", currentSeed, from_dist[currentSeed]);
					writer.write(tmpBuf);
				}
				else{
					char tmpBuf[50];
					sprintf(tmpBuf, " %d:inf ", currentSeed);
					writer.write(tmpBuf);
				}	
			}
			seeds.clear();
		}
		writer.write("\n");
	}
};

class SPCombiner: public Combiner<SPMsg> {
public:
	virtual void combine(SPMsg & old, const SPMsg & new_msg) {
		for(map<int, int>::const_iterator iter=new_msg.from_dist.begin(); iter != new_msg.from_dist.end(); iter++){
			int from = iter->first;
			int dist = iter->second;
			if(old.from_dist.find(from) == old.from_dist.end() || old.from_dist[from] > dist) {
				old.from_dist[from]=dist;
			}
		}
	}
};

void ghost_sssp(vector<set<int> > seeds, string in_path, string out_path, bool use_combiner, int _logSwitch = 1) {
	logSwitch = _logSwitch;
	if(logSwitch == 1){
		pid = (int) getpid();
		cout << "Worker " << get_worker_id() << " starts logging..." << endl;
		cout << "Worker pid: " << pid << endl;
	}
	batchedSeeds = seeds;
	batchNum = seeds.size();
	cout << "Batch: " << batchNum << endl;
	WorkerParams param;
	param.input_path = in_path;
	param.output_path = out_path;
	param.force_write = true;
	param.native_dispatcher = false;
	SPWorker_pregel worker;
	SPCombiner combiner;
	SPAgg agg;
	worker.setAggregator(&agg);
	if(use_combiner) worker.setCombiner(&combiner);
	worker.run(param);
}
