package org.apache.giraph.examples.io;
import java.util.List;
import java.util.ArrayList;

public class ListDoubleWritable implements org.apache.hadoop.io.WritableComparable {
  
  private List<Double> values;
  
  public ListDoubleWritable() {
    values=new ArrayList<Double>();
  }
  
  public ListDoubleWritable(List<Double> v) {
    values=new ArrayList<Double>();
    for(Double value: v){
      values.add(value);
    }
  }
  
  public void readFields(java.io.DataInput in) throws java.io.IOException {
    int size = in.readInt();
    for(int i=0;i<size;i++){
      values.add(in.readDouble());
    }
  }
  
  public void write(java.io.DataOutput out) throws java.io.IOException {
    out.writeInt(values.size());
    for(Double value: values)   out.writeDouble(value);
  }
  
  public void set(List<Double> v) {
    // for(Double value: v){
    //   values.add(value);
    // }
      values = v;
  }
  
  public List<Double> get() {
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