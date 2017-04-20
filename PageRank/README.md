# PageRank Calculation

To run the code:

0. Put the adjacent matrix file to `/tm` in HDFS; put the initial PageRank (every page is 1.0) to `/pr/0` in HDFS

1. Compile jave files
```bash
hadoop com.sun.tools.javac.Main *.java
```

2. Combine to a .jar file
```bash
jar cf pr.jar *.class
```

3. Run the .jar file
```bash
hadoop jar pr.jar Driver /tm/ /pr/ /output/ 40 0.2
```
This will run 40 iteration with `beta = 0.2`. The output results will be in `/pr/40`. Change the numbers as needed.

4. Copy the results to local disk
```
hdfs dfs -getmerge /pr/40/ results.txt
```

Alternatively, one can just name the adjacent matrix `tm.txt` and initial PageRank `pr.txt` and run the `run_pagerank.sh` file.
