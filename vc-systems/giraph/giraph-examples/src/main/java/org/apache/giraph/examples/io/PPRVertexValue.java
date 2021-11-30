package org.apache.giraph.examples.io;
import java.util.*;

public class PPRVertexValue implements org.apache.hadoop.io.WritableComparable {
  
  private Map<Long, Double> values;
  private List<ArrayList<Long>> localRandomWalks;
  private List<ArrayList<Long>> ph2LocalRandomWalks;
  private boolean phase3RcvMsgFlag;
  //private int currentBatch;

  
  
  public PPRVertexValue() {
    values=new HashMap<Long, Double>();
    localRandomWalks = new LinkedList<>();
    ph2LocalRandomWalks = new LinkedList<>();
    phase3RcvMsgFlag = false;
    //currentBatch = 0;
  }

  public PPRVertexValue(long initID, double initValue) {
    values=new HashMap<Long, Double>();
    values.put(initID, initValue);
    localRandomWalks = new LinkedList<>();
    ph2LocalRandomWalks = new LinkedList<>();
    phase3RcvMsgFlag = false;
    //currentBatch = 0;
  }

  public void putNewPPRValue(Long vertexID, Double value){
      values.put(vertexID, value);
  }
/*
  public void incCurrentBatch(){
      currentBatch += 1;
  }

  public int getCurrentBatch(){
       return currentBatch;
  }
 */ 
  public PPRVertexValue(Map<Long, Double> v) {
    values = v;
    localRandomWalks = new LinkedList<>();
    ph2LocalRandomWalks = new LinkedList<>();
    phase3RcvMsgFlag = false;
  }

    public boolean isPhase3RcvMsgFlag() {
        return phase3RcvMsgFlag;
    }

    public void setPhase3RcvMsgFlag(boolean phase3RcvMsgFlag) {
        this.phase3RcvMsgFlag = phase3RcvMsgFlag;
    }

    public List<ArrayList<Long>> getPh2LocalRandomWalks() {
        return ph2LocalRandomWalks;
    }

    public void setLocalRandomWalks(List<ArrayList<Long>> randomWalks){
      localRandomWalks = randomWalks;
    }

    public void setPh2LocalRandomWalks(List<ArrayList<Long>> ph2LocalRandomWalks) {
        this.ph2LocalRandomWalks = ph2LocalRandomWalks;
    }

    public List<ArrayList<Long>> getLocalRandomWalks() {
        return localRandomWalks;
    }

    public void setLocalRandomWalks(ArrayList<ArrayList<Long>> randomWalks){
      localRandomWalks = randomWalks;
    }

    public void readFields(java.io.DataInput in) throws java.io.IOException {
    int size = in.readInt();
    for(int i=0;i<size;i++){
        Long key = in.readLong();
        Double value = in.readDouble();
        values.put(key, value);
    }
  }
  
  public void write(java.io.DataOutput out) throws java.io.IOException {
    out.writeInt(values.size());
    for (Long key : values.keySet()) {
        out.writeLong(key);
        Double v = values.get(key);
        out.writeDouble(v);
    }
  }
  
  public void set(Map<Long, Double> v) {
    
    values =v;
  }
  
  public Map<Long, Double> get() {
    return values;
  }
  
  public boolean equals(java.lang.Object o) {
    return false;
  }
  
  public int hashCode() {
    return 0;
  }
  
  public int compareTo(java.lang.Object o) {
    return 0;
  }
  
  public java.lang.String toString() {
      String str ="";
      for(Long key: values.keySet()){
          str+=key;
          str+=":";
          str+=values.get(key);
          str+=";";
      }
    return str;
  }
  
  static {} {
  }
}
