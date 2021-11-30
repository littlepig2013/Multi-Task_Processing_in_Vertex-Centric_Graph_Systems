package org.apache.giraph.examples.io;

public class PPRBaselineMessageWritable implements org.apache.hadoop.io.WritableComparable {

    private Long sourceID;
    private Long targetID;
    private Boolean backFlag;

    public PPRBaselineMessageWritable() {

    }

    public PPRBaselineMessageWritable(Long sid, Long tid, Boolean flag) {
        sourceID = sid;
        targetID = tid;
        backFlag = flag;
    }

    public void readFields(java.io.DataInput in) throws java.io.IOException {
        sourceID=in.readLong();
        targetID=in.readLong();
        backFlag = in.readBoolean();
    }

    public void write(java.io.DataOutput out) throws java.io.IOException {
        out.writeLong(sourceID);
        out.writeLong(targetID);
        out.writeBoolean(backFlag);
    }

    public void set(Long sid, Long tid, Boolean flag) {
        sourceID = sid;
        targetID = tid;
        backFlag = flag;
    }

    public Long getSourceId() {
        return sourceID;
    }

    public Long getTargetId(){
        return targetID;
    }

    public Boolean getBackFlag() {
        return backFlag;
    }

    @Override
    public int compareTo(Object o) {
        return 0;
    }

    static {} {
    }
}
