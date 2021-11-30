package org.apache.giraph.examples.io;

import java.io.DataInput;
import java.io.DataOutput;
import java.io.IOException;
import java.util.HashMap;
import java.util.Map;

public class MSSPMessageWritable implements org.apache.hadoop.io.WritableComparable {

    private Map<Long, Double> values;

    public MSSPMessageWritable(){
        values = new HashMap<Long, Double>();
    }

    public MSSPMessageWritable(Map<Long, Double> values){
        this.values = values;
    }

    public void put(Long key, Double value){
        values.put(key,value);
    }

    public Map<Long, Double> getValues() {
        return values;
    }

    public void setValues(Map<Long, Double> values) {
        this.values = values;
    }

    @Override
    public String toString() {
        String str ="";
        for(Long key: values.keySet()){
            str+=key;
            str+=":";
            str+=values.get(key);
            str+=";";
        }
        return str;
    }

    @Override
    public void write(DataOutput out) throws IOException {
        out.writeInt(values.size());
        for (Long key : values.keySet()) {
            out.writeLong(key);
            Double v = values.get(key);
            out.writeDouble(v);
        }
    }

    @Override
    public void readFields(DataInput in) throws IOException {
        int size = in.readInt();
        for(int i=0;i<size;i++){
            Long key = in.readLong();
            Double value = in.readDouble();
            values.put(key, value);
        }
    }

    @Override
    public int compareTo(Object o) {
        return 0;
    }
}

