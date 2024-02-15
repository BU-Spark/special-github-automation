if [[ ! -d ./template ]];
then
    git clone git@github.com:BU-Spark/TEMPLATE-base-repo.git template
fi
mkdir working
cd working
cp -R ../template .
git clone $1 dest
mkdir -p ./dest/.github/workflows
cp -R ../template/.github/workflows/ ./dest/.github/workflows 
cd dest
# Create the collaborators file if it doesn't exist
if [[ ! -d ./COLLABORATORS ]];
then
    touch COLLABORATORS
fi
echo "git Status before"
git status
git add ./.github/*
git commit -m "Updated workflows with latest template"
git push origin
echo "Git status after"
git status
echo "Completed update"
cd ..
cd ..
rm -rf ./working
echo "Cleanup complete"