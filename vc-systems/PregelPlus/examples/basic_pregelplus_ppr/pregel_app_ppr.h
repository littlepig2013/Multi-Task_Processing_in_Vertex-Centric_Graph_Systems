#include "basic/pregel-dev.h"
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
#define LOG_FILE_NAME "log.txt"

int logSwitch;
int pid = 0;
int testBatch;
int numRWs = 256;
double unitPPR = 1.0/256;
vector<set<int> > batchedSeeds;
vector<int> batchedRWs;

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
//output line format: v \t v1:PPR1 v2:PPR2 ...

struct PPRValue_pregel
{
	vector<VertexID> edges;
	map<int, double> pprs;
};

ibinstream & operator<<(ibinstream & m, const PPRValue_pregel & v){;
	m<<v.edges;
	m<<v.pprs;
	return m;
}

obinstream & operator>>(obinstream & m, PPRValue_pregel & v){
	m>>v.edges;
	m>>v.pprs;
	return m;
}

struct PPRMsg_pregel
{
	VertexID source;
	VertexID target;
	bool backFlag;
};

ibinstream & operator<<(ibinstream & m, const PPRMsg_pregel & v){
	m<<v.source;
	m<<v.target;
	m<<v.backFlag;
	return m;
}

obinstream & operator>>(obinstream & m, PPRMsg_pregel & v){
	m>>v.source;
	m>>v.target;
	m>>v.backFlag;
	return m;
}


struct PPRAggType {
	int msgNum;
	bool finished_flag;
	PPRAggType (){
		msgNum = 0;
		finished_flag = true;
	}
};

ibinstream & operator<<(ibinstream & m, const PPRAggType & v) {
	m << v.msgNum;
	m << v.finished_flag;
	return m;
}

obinstream & operator>>(obinstream & m, PPRAggType & v) {
	m >> v.msgNum; 
	m >> v.finished_flag;
	return m;
}

//====================================

class PPRVertex_pregel:public Vertex<VertexID, PPRValue_pregel, PPRMsg_pregel>
{
	const double teleportationProbability = 0.20;

	private:
		void send_ppr_message(VertexID target, VertexID msg_source,VertexID msg_target, bool msg_backFlag){
			PPRMsg_pregel msg;
			msg.source = msg_source;
			msg.target = msg_target;
			msg.backFlag = msg_backFlag;
			send_message(target, msg);
		}
		void updateLocalPPRs(VertexID vertexId){
			if(value().pprs.find(vertexId) != value().pprs.end()){
				value().pprs[vertexId] += unitPPR;
			}else{
				value().pprs[vertexId] = unitPPR;
			}
		}
	public:
		int msgNum;
		bool finished_flag;

		virtual void compute(MessageContainer & messages)
		{
			int superstep = step_num() - 1;
			int numVertexes = get_vnum();
			int stepLimit = (int)((log (numVertexes))/teleportationProbability) + 1;
			
			msgNum = 0;
			finished_flag = false;
			srand((unsigned int) time (NULL)); 
			int currentBatch = (int)(superstep/(stepLimit+2));
			int currentBatchInnerStep = (int)(superstep%(stepLimit+2));
			/*
			int numRWsPerBatch = numRWs/testBatch;
			if(currentBatch == testBatch - 1){
				numRWsPerBatch += numRWs%testBatch;
			}*/
			int numRWsPerBatch = batchedRWs[currentBatch];
			if (currentBatchInnerStep == 0 && currentBatch < testBatch) {
				/*
				set<int> seeds = batchedSeeds[currentBatch];
				if(seeds.find(id) != seeds.end()){
					value().pprs[id] = 0.0;
					vector<VertexID> nextNeighborIds;

					for(int i = 0; i < numRWs; i++){
						double r = ((double) rand() / (RAND_MAX));  
						if(r <= teleportationProbability){
							value().pprs[id] += unitPPR;
						}else{
							int nextVertexIndex = (int) rand() % value().edges.size();
							nextNeighborIds.push_back(value().edges[nextVertexIndex]);
						}
					}
					msgNum += nextNeighborIds.size();
					for(int i = 0; i < nextNeighborIds.size(); i++){
						send_ppr_message(nextNeighborIds[i], id, nextNeighborIds[i], false);
					}
				}*/
				if(currentBatch == 0) value().pprs[id] = 0.0;
				vector<VertexID> nextNeighborIds;
				//cout << id << endl;
				for(int i = 0; i < numRWsPerBatch; i++){
					double r = ((double) rand() / (RAND_MAX));  
					if(r <= teleportationProbability){
						value().pprs[id] += unitPPR;
					}else{
						int nextVertexIndex = (int) rand() % value().edges.size();
						nextNeighborIds.push_back(value().edges[nextVertexIndex]);
					}
				}
				msgNum += nextNeighborIds.size();
				for(int i = 0; i < nextNeighborIds.size(); i++){
					send_ppr_message(nextNeighborIds[i], id, nextNeighborIds[i], false);
				}
				nextNeighborIds.clear();
				nextNeighborIds.resize(0);
				vector<VertexID> empty_neighbor;
				empty_neighbor.swap(nextNeighborIds);

			} else if (currentBatchInnerStep < stepLimit && currentBatch < testBatch) {
				for(int i = 0; i < messages.size(); i++){
					bool backFlag = messages[i].backFlag;
					VertexID source = messages[i].source;
					VertexID target = messages[i].target;
					if(backFlag){
						updateLocalPPRs(source);
					}else{
						msgNum++;
						double r = ((double) rand() / (RAND_MAX)); 
						if(r <= teleportationProbability){
							send_ppr_message(source, id, source, true);
						}else{
							int nextVertexIndex = (int) rand() % value().edges.size();
							VertexID nextVertexID = value().edges[nextVertexIndex];
							send_ppr_message(nextVertexID, source, nextVertexID, false);
						}
					}
				}
			} else if (currentBatchInnerStep == stepLimit && currentBatch < testBatch ){
				for(int i = 0; i < messages.size(); i++){
					bool backFlag = messages[i].backFlag;
					VertexID source = messages[i].source;
					if(backFlag){
						updateLocalPPRs(source);
					}else{
						send_ppr_message(source, id, source, true);
						msgNum++;
					}
				}
			} else if (currentBatchInnerStep == stepLimit + 1 && currentBatch < testBatch){
				for(int i = 0; i < messages.size(); i++){
					updateLocalPPRs(messages[i].source);
				}
				finished_flag = true;

			} else if (currentBatch >= testBatch){
				vote_to_halt();
			}

		}
};


class PPRAgg: public Aggregator<PPRVertex_pregel, PPRAggType,PPRAggType> {
private:
	PPRAggType	value;
	int num_batch;
public:
	virtual void init() {
		value.msgNum = 0;
		value.finished_flag = true;
		num_batch = 0;
	}

	virtual void stepPartial(PPRVertex_pregel* v){
		value.msgNum += v->msgNum;
		value.finished_flag = value.finished_flag & v->finished_flag;

	}

	virtual void stepFinal(PPRAggType* p){
		value.msgNum += p->msgNum;
		value.finished_flag = value.finished_flag & p->finished_flag;

	}

	virtual PPRAggType* finishPartial(){
		if(logSwitch == 1){
			string s1="VmHWM";
			string s2="VmRSS";
			cout << _my_rank << " sent " << value.msgNum << " messages in this superstep" << endl;
			ofstream fout ("mem-log.txt", ofstream::out|ofstream::app);
			stringstream ss;
			ss << _my_rank;	
			fout << num_batch << " " + ss.str() + " " + get_memory_info(s1) << endl;
			fout << num_batch << " " + ss.str() + " " + get_memory_info(s2) << endl;
			fout.close();
		}
		return &value;
	}

	virtual PPRAggType* finishFinal(){
		if(value.finished_flag){
			//time_t t = std::time(0);
			//tm* now = std::localtime(&t);
			//ofstream fout(LOG_FILE_NAME, ofstream::out| ofstream::app);
			//system("python log_aggregator.py");
			//fout << "[LOG] Batch " << num_batch << " " << readAggregates() << " curr_time: " << now->tm_hour <<"-" << now->tm_min <<"-" << now->tm_sec << endl;
			//fout.close();
			num_batch++;

		}
		return &value;
	}

};

class PPRWorker_pregel:public Worker<PPRVertex_pregel, PPRAgg>
{
	char buf[400];

	public:
		//C version
		virtual PPRVertex_pregel* toVertex(char* line)
		{
			char * pch;
			pch=strtok(line, "\t");
			PPRVertex_pregel* v=new PPRVertex_pregel;
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

		virtual void toline(PPRVertex_pregel* v, BufferedWriter & writer)
		{
			sprintf(buf, "%d\t", v->id);
			writer.write(buf);
			for(map<VertexID, double>::iterator iter = v->value().pprs.begin(); iter != v->value().pprs.end(); iter++){
				/*if(iter->second < E){
					continue;
				}*/
				char tmpBuf[50];
				sprintf(tmpBuf, " %d:%.5f", iter->first, iter->second);
				writer.write(tmpBuf);
			}
			writer.write("\n");
		}
};

void pregel_ppr(vector<int> _batchedRWs, string in_path, string out_path, int _logSwitch = 0, bool unitPPRFlag=true)
//void pregel_ppr(string in_path, string out_path, int _testBatch, int _numRWs, int _logSwitch = 0)
//void pregel_ppr(vector<set<int> > _batchedSeeds, string in_path, string out_path, int _logSwitch = 0)
{
	//numRWs = _numRWs;
	numRWs = 0;
	batchedRWs = _batchedRWs;
	for(int  i =0; i < batchedRWs.size();i++){
		numRWs += batchedRWs[i];
	}
	cout << numRWs << endl;
	testBatch = batchedRWs.size();
	if(unitPPRFlag){
		unitPPR = 1.0/numRWs;
	}else{
		unitPPR = 1.0;
	}
	//unitPPR = 1.0/numRWs;
	//unitPPR = 1.0/128;
	//testBatch = _testBatch;
	//testBatch = _batchedSeeds.size();
	//batchedSeeds = _batchedSeeds;
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
	PPRWorker_pregel worker;
	PPRAgg agg;
	worker.setAggregator(&agg);
	worker.run(param);
}

