#!/bin/bash
echo "Network overuse time (Avg):"
grep -r "Avg overuse time" -A1 $1| awk -F' ' 'BEGIN{i=0}{if(i%3==1)print $(NF-1); i+=1}'
echo "Network overuse time (Max):"
grep -r "Max overuse time" -A1 $1|awk -F' ' 'BEGIN{i=0}{if(i%3==1)print $(NF-1); i+=1}'
echo "Total time:"
grep "Total time" $1| awk -F' ' '{print $(NF-1)}'
echo "Disk overuse time:"
grep -r "Max overuse IO " $1 | awk -F':' '{print $2}'
echo "Avg percentage of 100 for all machines:"
grep -r "Avg percentage of 100 for all machines" $1 | awk -F':' '{print $2}'
echo "Max disk util:"
grep -r "Final Max" $1 | awk -F':' '{print $2}'
echo "Max avg-qu-sz:"
grep -r "Max avgqu-sz" $1 | awk -F':' '{print $2}'
echo "Avg avg-qu-sz:"
grep -r "Avg avgqu-sz" $1 | awk -F':' '{print $2}'
