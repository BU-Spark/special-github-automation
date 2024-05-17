echo "Adding archive tag"
git clone $2 dest
cd dest
git tag -a spark-archive-$1 -m "Spark! Project Archive $1"
git push origin spark-archive-$1
cd ..
rm -rf ./dest