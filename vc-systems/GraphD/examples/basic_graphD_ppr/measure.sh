
#!/bin/bash

slaves=()


type=$1


if [ "$type" = "start" ];then
	for slave in "${slaves[@]}"
	do
		ssh $slave 'nohup iostat -xdk 1 -p sda > ~/vc-systems/GraphD/examples/basic_graphD_ppr/io_output_test.txt &'
		
	done
elif [ "$type" = "measure" ];then
	echo -e "\n IO Usage"	
	rm -f "io_tmp_stat.txt"
	for slave in "${slaves[@]}"
	do
		ssh $slave 'cat ~/vc-systems/GraphD/examples/basic_graphD_ppr/io_output_test.txt' > $slave"_io_tmp.txt"
		echo -e "=================================================================" >> "io_tmp_stat.txt"
		echo -e $slave >> "io_tmp_stat.txt"
		echo -e "-----------------------------------------------------------------" >> "io_tmp_stat.txt"
		cat $slave"_io_tmp.txt" | grep --text "sda" | awk 'BEGIN{max_util=0;max=0;total=0;total_ww=0;util_100_counter=0;util_90_100_counter=0;util_0_39_counter=0;util_40_69_counter=0;util_70_89_counter=0;total_util=0;i=0;tt_avgrq_sz=0;tt_avgqu_sz=0;io_stat=$0}{i+=1;total_ww+=$5;tmp=$7+$6;total+=tmp;tt_avgrq_sz+=$8;tt_avgqu_sz+=$9;total_util+=$NF;if(tmp>max) {max=tmp;io_stat=$0;} if($NF > max_util) {max_util=$NF;}if($NF >= 90) {util_90_100_counter += 1;if($NF >= 100){util_100_counter += 1;}} else if($NF >= 70) {util_70_89_counter += 1} else if($NF >= 40) {util_40_69_counter+= 1} else {util_0_39_counter += 1}}END{print " io_stat:" io_stat "\n total: " total "\n lines: " i "\n Avg: " total*1.0/i "\n Avg_ww: " total_ww*1.0/i"\n Max: " max "\n Avg_util: " total_util*1.0/i "\n Max Util: " max_util "\n Util Stats: \n 0-39: "  util_0_39_counter*1.0/i "\n 40-69: " util_40_69_counter*1.0/i "\n 70-89: " util_70_89_counter "\n 90-100: " util_90_100_counter "\n >= 100: " util_100_counter"\n Avgrq-sz: " tt_avgra_sz*1.0/i "\n Avgqu-sz: " tt_avgqu_sz*1.0}'  >> "io_tmp_stat.txt"
		rm $slave"_io_tmp.txt"
		echo -e "=================================================================" >> "io_tmp_stat.txt"
		
	done
	cat io_tmp_stat.txt | grep --text "Max Util" | awk -F':' 'BEGIN{total=0;i=0;max=0;}{total += $2;i += 1;if($2 > max) {max=$2;}}END{print "Final Max util: " max "\nFinal Max Avg util: "total*1.0/i}' > max_util.txt
	cat io_tmp_stat.txt | grep --text "Avgrq-sz" | awk -F':' 'BEGIN{total=0;i=0;max=0;}{total += $2;i += 1;if($2 > max) {max=$2;}}END{print "Max avgrq-sz: " max "\nAvg avgrq-sz: "total*1.0/i}' >> max_util.txt
	cat io_tmp_stat.txt | grep --text "Avgqu-sz" | awk -F':' 'BEGIN{total=0;i=0;max=0;}{total += $2;i += 1;if($2 > max) {max=$2;}}END{print "Max avgqu-sz: " max "\nAvg avgqu-sz: "total*1.0/i}' >> max_util.txt
	cat io_tmp_stat.txt | grep ">= 100" | awk -F':' 'BEGIN{total=0;i=0;max=0}{total += $2;i += 1;if($2 > max){max=$2;}}END{print "Avg percentage of 100 for all machines: " total*1.0/i"\nMax overuse IO count: " max}' >> max_util.txt

elif [ "$type" = "stop" ];then
	for slave in "${slaves[@]}"
	do
		ssh $slave "killall iostat"
	done
elif [ "$type" = "delete" ];then
	for slave in "${slaves[@]}"
	do
		ssh $slave "rm ~/vc-systems/GraphD/examples/basic_graphD_ppr/io_output_test.txt"
	done


fi

