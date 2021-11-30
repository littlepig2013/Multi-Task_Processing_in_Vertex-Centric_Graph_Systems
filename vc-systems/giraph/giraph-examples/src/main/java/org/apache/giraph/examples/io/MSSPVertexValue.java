package org.apache.giraph.examples.io;

import org.apache.commons.collections.map.HashedMap;

import java.io.DataInput;
import java.io.DataOutput;
import java.io.IOException;
import java.util.Map;

public class MSSPVertexValue implements org.apache.hadoop.io.WritableComparable {
    private Map<Long, Double> values;

    public MSSPVertexValue(Map<Long, Double> values){
        this.values = values;
    }

    public MSSPVertexValue(){
        values = new HashedMap();
    }

    public Map<Long, Double> getValues() {
        return values;
    }

    public void setValues(Map<Long, Double> values) {
        this.values = values;
    }

    public void putNewMSSPValue(Long key, Double value){
        this.values.put(key,value);
    }

    @Override
    public String toString() {
        return super.toString() + ":" + values.toString();
    }

    @Override
    public int compareTo(Object o) {
        return 0;
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
    public void write(DataOutput out) throws IOException {
        out.writeInt(values.size());
        for (Long key : values.keySet()) {
            out.writeLong(key);
            Double v = values.get(key);
            out.writeDouble(v);
        }
    }
}

