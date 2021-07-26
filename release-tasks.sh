echo "======== DOWNLOADING ANT ========"
echo ""

curl https://downloads.apache.org/ant/binaries/apache-ant-1.10.11-bin.tar.gz --output ant/apache-ant.bin.tar.gz
tar -xvf ant/apache-ant.bin.tar.gz -C ant
ls -al ant | grep ant
ls -al ant/apache-ant-1.10.11
echo "======== ANT DOWNLOADED ========"
echo ""

echo "======== UPDATING 'PATH' ========"
echo ""
export _PATH=$PATH
export PATH=$PATH:/ant/apache-ant-1.10.11/lib:ant/apache-ant-1.10.11/bin
env
echo $PATH
