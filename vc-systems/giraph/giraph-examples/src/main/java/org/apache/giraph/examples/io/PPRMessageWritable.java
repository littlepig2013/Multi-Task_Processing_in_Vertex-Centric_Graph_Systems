package org.apache.giraph.examples.io;


public class PPRMessageWritable implements org.apache.hadoop.io.WritableComparable {
  
  private Long sourceID;
  private Long targetID;
  private Long propagate;//number of rws from sourceID to targetID
  private Long randomWalkID;
  
  public PPRMessageWritable() {
    
  }
  
  public PPRMessageWritable(Long sid, Long tid, Long p, Long rwID) {
    sourceID = sid;
    targetID = tid;
    propagate=p;
    randomWalkID=rwID;
  }
  
  public void readFields(java.io.DataInput in) throws java.io.IOException {
    sourceID=in.readLong();
    targetID=in.readLong();
    propagate=in.readLong();
    randomWalkID=in.readLong();
  }
  
  public void write(java.io.DataOutput out) throws java.io.IOException {
    out.writeLong(sourceID);
    out.writeLong(targetID);
    out.writeLong(propagate);
    out.writeLong(randomWalkID);
  }
  
  public void set(Long sid, Long tid, Long p, Long rwID) {
    sourceID = sid;
    targetID = tid;
    propagate = p;
    randomWalkID=rwID;
  }
  
  public Long getSourceId() {
    return sourceID;
  }

  public Long getTargetId(){
      return targetID;
  }

  public Long getPropagate(){
      return propagate;
  }

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