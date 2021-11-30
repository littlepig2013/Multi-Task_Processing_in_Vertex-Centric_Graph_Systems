#include "pregel_app_khop.h"
#include "stdlib.h"
#include <iostream>
#include <fstream>
#include <vector>
#include <set>
#include <string>


#define INPUT_FILE_NAME "batchedSeeds.txt"
#define INPUT_FILE_NAME2 "batchedWorkload.txt"


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

void getBatchedRWs(string fileName, vector<int> & batchedRWs){
	string line;
	batchedRWs.clear();
	ifstream batchedRWsIn(fileName.c_str(), ios::in);
	while(getline(batchedRWsIn, line)){
		batchedRWs.push_back(atoi(line.c_str()));
	}
	batchedRWsIn.close();
}


int main(int argc, char* argv[]){
	int logSwitch = 0;
	string output_path = "/pregelplus_output";
	vector<set<int> > batchedSeeds;
	getBatchedSeeds(INPUT_FILE_NAME, batchedSeeds);
	int k = 2;
	if(argc >= 2){
		logSwitch = atoi(argv[1]) == 1 ? 1 : 0;
		//unitPPRFlag = atoi(argv[3]) == 1 ? true:false;
	}
	if(argc >= 3){
		output_path = argv[2];
	}
	if(argc >= 4){
		k = atoi(argv[3]);
	}
	
	init_workers();
	pregel_khop(batchedSeeds, "/dblp_pregelplus", output_path, k, logSwitch);
	//pregel_ppr("/blogel_input", "/blogel_output", testBatch, numRWs, logSwitch);
	//pregel_ppr(batchedSeeds, "/blogel_input", "/blogel_output", logSwitch);
	worker_finalize();

	return 0;
}
