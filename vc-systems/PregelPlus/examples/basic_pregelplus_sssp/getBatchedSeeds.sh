#!/bin/bash
inputFile="originSeeds.txt"
tmpInputFile="originSeeds32.txt"
outputFile="batchedSeeds.txt"
seedsNum=`wc -l $inputFile | awk '{print $1}'`
#echo $seedsNum
batch=$1
seedsNum=$2

if [ -z "$batch" ]
then
	batch=1
fi

if [ $# -eq 3 ]
then
	outputFile=$3
fi

if [ -z "$seedsNum" ]
then
	seedsNum=32
	tmpInputFile="originSeeds32.txt"
else
	tmpInputFile="originSeeds"$seedsNum".txt"
fi

cat $inputFile | sort -R | head -$seedsNum > $tmpInputFile

if [ -e "$outputFile" ] 
then
	rm $outputFile
fi

size=`expr $seedsNum / $batch`
#echo $size
testSeeds=`expr $size \* $batch`
#echo $testSeeds

if [ $testSeeds -lt $seedsNum ]
then 
	size=`expr $size + 1`
fi
currentBatch=0
while [ $currentBatch -le $batch ]
do
	leftSeeds=`expr $seedsNum - $currentBatch \* $size`	
	if [ $leftSeeds -lt $size ]
	then
		tail -$leftSeeds $tmpInputFile | awk '{print $1"\t"'$currentBatch'}' >> $outputFile
	else
		tail -$leftSeeds $tmpInputFile | head -$size | awk '{print $1"\t"'$currentBatch'}' >> $outputFile
	fi
	currentBatch=`expr $currentBatch + 1`
done



if [ -e "$tmpInputFile" ] 
then
	rm $tmpInputFile
fi
