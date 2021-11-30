package org.apache.giraph.examples.io;


import java.util.ArrayList;

public class PPRDoublingMessageWritable implements org.apache.hadoop.io.WritableComparable {
  
  private Long sourceID;
  private Long targetID;
  //private Long propagate;//number of rws from sourceID to targetID
  private int length;
  private ArrayList<Long> data;
  private Long randomWalkID;
  private int remainNumWalks;
  public PPRDoublingMessageWritable() {
    
  }
  
  public PPRDoublingMessageWritable(Long sid, Long tid, int l, ArrayList<Long> d, Long rwID) {
    sourceID = sid;
    targetID = tid;
    length = l;
    data = d;
    randomWalkID=rwID;
    remainNumWalks = 0;
  }

  public PPRDoublingMessageWritable(Long sid, Long tid, int l, ArrayList<Long> d, Long rwID, int rNumWalks) {
        sourceID = sid;
        targetID = tid;
        length = l;
        data = d;
        randomWalkID=rwID;
        remainNumWalks = rNumWalks;
     }
  
  public void readFields(java.io.DataInput in) throws java.io.IOException {
    sourceID=in.readLong();
    targetID=in.readLong();
    length = in.readInt();
    data = new ArrayList<>();
    for(int i = 0; i < length; i++){
        data.add(in.readLong());
    }
    randomWalkID=in.readLong();
    remainNumWalks = in.readInt();
  }
  
  public void write(java.io.DataOutput out) throws java.io.IOException {
    out.writeLong(sourceID);
    out.writeLong(targetID);
    out.writeInt(length);
    for(int i = 0; i < length; i++){
        out.writeLong(data.get(i));
    }
    out.writeLong(randomWalkID);
    out.writeInt(remainNumWalks);
  }
  
  public void set(Long sid, Long tid, int l, ArrayList<Long> d, Long rwID) {
    sourceID = sid;
    targetID = tid;
    length = l;
    data = d;
    randomWalkID=rwID;
  }

  public int getRemainNumWalks() {
    return remainNumWalks;
  }

  public Long getSourceId() {
    return sourceID;
  }

  public Long getTargetId(){
      return targetID;
  }

  public int getLength() { return length; }

  public ArrayList<Long> getData() { return data; }

  public Long getRandomWalkId(){
    return randomWalkID;
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
    return null;
  }
  
  static {} {
  }
}