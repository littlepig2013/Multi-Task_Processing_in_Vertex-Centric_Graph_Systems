package org.apache.giraph.examples.io;
import java.util.HashMap;
import java.util.Map;

public class HashDoubleWritable implements org.apache.hadoop.io.WritableComparable {
  
  private Map<Long, GenericPair<Integer, Double> > values;

  
  
  public HashDoubleWritable() {
    values=new HashMap<Long, GenericPair<Integer,Double> >();
  }
  
  public HashDoubleWritable(Map<Long, GenericPair<Integer, Double> > v) {
    // values=new HashMap<Long, GenericPair<Integer, Double> >();
    // for (Long key : v.keySet()) {
        
    //     values.put(key, v.get(key));
    
    // }
    values = v;
    
  }
  
  public void readFields(java.io.DataInput in) throws java.io.IOException {
    int size = in.readInt();
    for(int i=0;i<size;i++){
        Long key = in.readLong();
        Integer value1 = in.readInt();
        Double value2 = in.readDouble();
        GenericPair<Integer, Double> gp = new GenericPair<>(value1, value2);
        values.put(key, gp);
    }
  }
  
  public void write(java.io.DataOutput out) throws java.io.IOException {
    out.writeInt(values.size());
    for (Long key : values.keySet()) {
        out.writeLong(key);
        GenericPair<Integer, Double> v = values.get(key);
        out.writeInt(v.getFirst());
        out.writeDouble(v.getSecond());
    }
  }
  
  public void set(Map<Long, GenericPair<Integer, Double> > v) {
    // for (Long key : v.keySet()) {
        
    //     values.put(key, v.get(key));
    
    // }
    values =v;
  }
  
  public Map<Long, GenericPair<Integer, Double> > get() {
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
    return null;
  }
  
  static {} {
  }
}