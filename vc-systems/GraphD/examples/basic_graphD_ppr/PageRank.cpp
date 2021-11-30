#include "stdlib.h"
#include <cmath>
#include <iostream>
#include <fstream>
#include <vector>
#include <set>
#include <string>
#include <ctime>


#include "Vertex.h"
#include "Comper.h"
#include "Runner.h"
#include "Combiner.h"

#define PAGERANK_ROUND 10
#define INPUT_FILE_NAME "batchedSeeds.txt"
#define INPUT_FILE_NAME2 "batchedRWs.txt"
#define IO_STAT_FILE_NAME "max_util.txt"
#define LOG_FILE_NAME "log.txt"

int pid = 0;
int testBatch;
int numRWs = 256;
double unitPPR = 1.0/256;
vector<set<int> > batchedSeeds;
vector<int> batchedRWs;


using namespace std;

vector<string> split(string str, string separator){
	vector<string> result;
	int cutAt;
	while( (cutAt = str.find_first_of(separator)) != str.npos ){
		if(cutAt > 0){
			result.push_back(str.substr(0, cutAt));
		}else{
			result.push_back("");
		}
		str = str.substr(cutAt + 1);
	}

	if(str.length() > 0){
		result.push_back(str);
	}else{
		result.push_back("");
	}

	return result;
}

void getBatchedSeeds(string fileName, vector<set<int> > & batchedSeeds){
	string line;
	ifstream batchedSeedsIn(fileName.c_str(), ios::in);
	int previous_batch = -1;
	while(getline(batchedSeedsIn, line)){
		vector<string> strs = split(line, "\t");
		int id = atoi(strs[0].c_str());
		int batch = atoi(strs[1].c_str());
		if(previous_batch != batch){
			batchedSeeds.push_back(set<int>());
		}
		batchedSeeds[batch].insert(id);
		previous_batch = batch;	
	}
	batchedSeedsIn.close();

}


double getMaxUtil(string filename){
	string line;
	ifstream maxUtilIn(filename.c_str(), ios::in);
	double util;
	int count = 0;
	while(getline(maxUtilIn, line)){
		vector<string> strs = split(line, ":");
		if(strs[0].compare("Final Max Avg util") == 0){
			util = atof(strs[1].c_str());
			cout << strs[0] << " " << strs[1] << endl;
			count++;
		}

		if(strs[0].compare("Avg percentage of 100 for all machines") == 0){
			cout << strs[0] << " " << strs[1] << endl;
			count++;
		}

		if(strs[0].compare("Max overuse IO count") == 0){
			cout << strs[0] << " " << strs[1] << endl;
			count++;
		}

		if(count >= 3){
			break;
		}
	}
	maxUtilIn.close();
	return util;
}

void getBatchedRWs(string fileName, vector<int> & batchedRWs){
	string line;
	batchedRWs.clear();
	ifstream batchedRWsIn(fileName.c_str(), ios::in);
	while(getline(batchedRWsIn, line)){
		batchedRWs.push_back(atoi(line.c_str()));
	}
	batchedRWsIn.close();
}

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

struct PPRValue_pregel
{
	vector<VertexID> edges;
	map<VertexID, double> pprs;
};

ibinstream & operator>>(ibinstream & m, PPRValue_pregel & v){
	
	m>>v.edges;	
	m>>v.pprs;
	return m;
}

obinstream & operator<<(obinstream & m, const PPRValue_pregel & v){
	m<<v.edges;	
	m<<v.pprs;
	return m;
}

ifbinstream & operator>>(ifbinstream & m, PPRValue_pregel & v){
	m>>v.edges;
	m>>v.pprs;
	return m;
}

ofbinstream & operator<<(ofbinstream & m, const PPRValue_pregel & v){
	m<<v.edges;	
	m<<v.pprs;
	return m;
}

struct PPRMsg_pregel
{
	VertexID source;
	VertexID target;
	bool backFlag;
};

ibinstream & operator>>(ibinstream & m, PPRMsg_pregel & v){
	m>>v.source;
	m>>v.target;
	m>>v.backFlag;
	return m;
}

obinstream & operator<<(obinstream & m, const PPRMsg_pregel & v){
	m<<v.source;
	m<<v.target;
	m<<v.backFlag;
	return m;
}


ifbinstream & operator>>(ifbinstream & m,  PPRMsg_pregel & v){
	m>>v.source;
	m>>v.target;
	m>>v.backFlag;
	return m;
}

ofbinstream & operator<<(ofbinstream & m, const PPRMsg_pregel & v){
	m<<v.source;
	m<<v.target;
	m<<v.backFlag;
	return m;
}

struct PPRAggValue
{
	int status_code; // 0 -> init, 1 -> batch finished, 2 -> total finished, -1 -> others
	long long msgNum;
	PPRAggValue() {
		status_code = 0;
		msgNum = 0;
	}
};

ibinstream & operator>>(ibinstream & m, PPRAggValue & v){
	m >> v.status_code;
	m >> v.msgNum;
	return m;
}
obinstream & operator<<(obinstream & m, const PPRAggValue & v){
	m << v.status_code;
	m << v.msgNum;
	return m;
}
ifbinstream & operator>>(ifbinstream & m, PPRAggValue & v){
	m >> v.status_code;
	m >> v.msgNum;
	return m;
}
ofbinstream & operator<<(ofbinstream & m, const PPRAggValue & v){
	m << v.status_code;
	m << v.msgNum;
	return m;
}
/*
class PRCombiner:public Combiner<double>
{
	public:
		virtual void combine(double& old, const double& new_msg)
		{
			old += new_msg;
		}
};*/

class PRVertex:public Vertex<VertexID, PPRValue_pregel, VertexID, PPRMsg_pregel> //no combiner
//class PRVertex:public Vertex<VertexID, PPRValue_pregel, VertexID, PPRMsg_pregel, PRCombiner> //with combiner
{

	double teleportationProbability = 0.20;

	private:
		void send_ppr_message(VertexID target, VertexID msg_source,VertexID msg_target, bool msg_backFlag){
			PPRMsg_pregel msg;
			msg.source = msg_source;
			msg.target = msg_target;
			msg.backFlag = msg_backFlag;
			send_message(target, msg);
		}
		void updateLocalPPRs(VertexID vertexId){
			if(value.pprs.find(vertexId) != value.pprs.end()){
				value.pprs[vertexId] += unitPPR;
			}else{
				value.pprs[vertexId] = unitPPR;
			}
		}

	public:
		int status_code;
		long long msgNum;
		virtual void compute(vector<PPRMsg_pregel>& messages, vector<VertexID>& edges)
		{
			status_code = -1;
			msgNum = 0;
			int superstep = step_num() - 1;
			int numVertexes = 613586;
			int stepLimit = (int)((log (numVertexes))/teleportationProbability) + 1;
			
			srand((unsigned int) time (NULL)); 
			int currentBatch = (int)(superstep/(stepLimit+2));
			int currentBatchInnerStep = (int)(superstep%(stepLimit+2));
			/*
			int numRWsPerBatch = numRWs/testBatch;
			if(currentBatch == testBatch - 1){
				numRWsPerBatch += numRWs%testBatch;
			}*/
			int numRWsPerBatch = batchedRWs[currentBatch];
			//cout << "test 2" << endl;
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
				value.pprs[id] = 0.0;
				vector<VertexID> nextNeighborIds;
				//cout << id << endl;
				for(int i = 0; i < numRWsPerBatch; i++){
					double r = ((double) rand() / (RAND_MAX));  
					if(r <= teleportationProbability){
						value.pprs[id] += unitPPR;
					}else{
						int nextVertexIndex = (int) rand() % edges.size();
						nextNeighborIds.push_back(edges[nextVertexIndex]);
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
				if(currentBatch == 0){
					status_code = 0;
				}

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
							int nextVertexIndex = (int) rand() % edges.size();
							VertexID nextVertexID = edges[nextVertexIndex];
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
				status_code = 1;

			} else if (currentBatch >= testBatch){
				vote_to_halt();
				status_code = 2;
			}
			/*

			if(step_num()==1)
			{
				value = 1.0;
			}
			else
			{
				double sum = 0;
				for(int i=0; i<msgs.size(); i++) sum += msgs[i];
				value = 0.15 + 0.85*sum;
			}
			if(step_num() < PAGERANK_ROUND)
			{
				double msg = value / degree; //value is double, so division gives double
				for(int i=0; i<edges.size(); i++) send_message(edges[i], msg);
			}
			else vote_to_halt();
			*/
		}
};

class PPRAgg: public Aggregator<PRVertex, PPRAggValue, PPRAggValue> {
	int batch;
	PPRAggValue agg;
public:
	PPRAgg(){ batch = 0; agg = PPRAggValue();}
	virtual void init(){agg.status_code = 2;}
	virtual void stepPartial(PRVertex *v, EdgeContainer & edges){
		agg.status_code = agg.status_code < v->status_code ? agg.status_code : v->status_code;
		agg.msgNum += v->msgNum;
	}
	virtual void stepFinal(PPRAggValue* p){
		agg.status_code = agg.status_code < p->status_code ? agg.status_code : p->status_code;
		agg.msgNum += p->msgNum;
	}
	virtual PPRAggValue* finishPartial(){
		return &agg;
	}

	virtual PPRAggValue* finishFinal() {
		if(agg.status_code > 1) cout << "#Messages: " << agg.msgNum << endl;
		/*
		if (agg.status_code == 0){
			system("bash measure.sh start");
		}else if (agg.status_code >= 1){
			time_t t = std::time(0); 
			tm* now = std::localtime(&t);
			ofstream fout (LOG_FILE_NAME, ofstream::out | ofstream::app);
			system("bash measure.sh stop");
			system("bash measure.sh measure");
			//system("bash measure.sh delete");
			double util = getMaxUtil(IO_STAT_FILE_NAME);
			fout << "[LOG] Batch " << batch << " Util: " << util << "\% curr_time: " << now->tm_hour <<"-" << now->tm_min <<"-" << now->tm_sec  << endl;
			cout << "[LOG] Batch " << batch << " Util: " << util << "\% curr_time: " << now->tm_hour <<"-" << now->tm_min <<"-" << now->tm_sec  << endl;
			batch += 1;
			if(agg.status_code == 1){
				system("bash measure.sh start");
			}
			//system("rm max_util.txt");
			fout.close();
		}*/
		
		return &agg;
	}
};


class PRComper:public Comper<PRVertex, PPRAgg>
{
	char buf[100];

	public:
		virtual VertexID parseVertex(char* line, obinstream& file_stream)
		{
			char * pch = strtok(line, "\t");
			VertexID id = atoll(pch);
			PPRValue_pregel value;
			
			file_stream << id; //write <I>
			//file_stream << 1.0; //write <V>, init Pr = 1.0 (cannot use 1 as it is not double)
			pch=strtok(NULL, " ");
			int num=atoi(pch);
			for(int i=0; i<num; i++){
				pch=strtok(NULL, " ");
				VertexID nb = atoll(pch);
				value.edges.push_back(nb);
			}
			file_stream << value;
			file_stream << true; //write <active>
			file_stream << num; //write numNbs
			for(int i=0; i<num; i++)
			{
				file_stream << value.edges[i]; //write <E>
				
			}
			return id;
		}

		virtual void to_line(PRVertex& v, ofstream& fout)
		{
			fout<<v.id<<'\t'; //report: vid \t pagerank
			fout.precision(5);
			for(map<VertexID, double>::iterator iter = v.value.pprs.begin(); iter != v.value.pprs.end(); iter++){
				/*if(iter->second < E){
					continue;
				}*/
				fout << iter->first << ":" << iter->second;
			}
			fout << endl;
		}

		virtual void to_line(PRVertex& v, BufferedWriter& fout)
		{
			sprintf(buf, "%d\t", v.id);
			fout.write(buf);
			for(map<VertexID, double>::iterator iter = v.value.pprs.begin(); iter != v.value.pprs.end(); iter++){
				/*if(iter->second < E){
					continue;
				}*/
				char tmpBuf[50];
				sprintf(tmpBuf, " %d:%.5f", iter->first, iter->second);
				fout.write(tmpBuf);
			}
			fout.write("\n");
		}
};

int main(int argc, char* argv[])
{
	numRWs = 0;
	getBatchedRWs(INPUT_FILE_NAME2, batchedRWs);
	for(int  i =0; i < batchedRWs.size();i++){
		numRWs += batchedRWs[i];
	}
	cout << numRWs << endl;
	testBatch = batchedRWs.size();
	unitPPR = 1.0/numRWs;

	Runner<PRVertex, PRComper> runner;
	string hdfs_inpath = argv[1];
	string hdfs_outpath = "/graphd_output";
	string local_root = "/root/vc-systems/GraphD/examples/basic_graphD_ppr/iopregel_localspace";
	bool dump_with_edges = false;
	runner.runHH(hdfs_inpath, hdfs_outpath, local_root, dump_with_edges, argc, argv); //HDFS Load, HDFS Dump
    return 0;
}
