#!/bin/bash
# clean up
hdfs dfs -rm -r /tm
hdfs dfs -mkdir /tm
hdfs dfs -put tm.txt /tm
hdfs dfs -rm -r /output
hdfs dfs -rm -r /pr
hdfs dfs -mkdir /pr
hdfs dfs -mkdir /pr/0
hdfs dfs -put pr.txt /pr/0
# run
hadoop com.sun.tools.javac.Main *.java
jar cf pr.jar *.class
hadoop jar pr.jar Driver /tm/ /pr/ /output/ 40 0.2
# get results
hdfs dfs -getmerge /pr/40/ results.txt
