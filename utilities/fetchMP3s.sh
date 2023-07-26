#!/bin/bash
declare -A newmap
newmap[t1]="1SFv3MOqujXB7ZzNKV6Jm2EgE_xRvAsli"
newmap[t2]="17HaUXIylErTJDI0ow7q-j25CfUbD8ViC"
newmap[t3]="1nQQbdpwkIh7eCv0-Zohfnyk-5Ev7zCNz"
newmap[t4]="1Oda5lZ8iXJ_Ut1DdoS_wwfOqmnAsZeKw"
newmap[t5]="1rQPS8hbDz3cvFprSaqY7sX10vA79EskM"

OUTDIR=/ort_mp3s
if [ -z "$IS_DOCKER" ]; then
    OUTDIR=ORT_MP3s.recoded
fi

STARTDIR=$(pwd)
mkdir -p $STARTDIR/data
#gdown https://drive.google.com/uc?id=${newmap[t5]}
for tname in t1 t2 t3 t4 t5; do
  outname="ORT_MP3s.recoded.${tname}.tar"
  gdown --id ${newmap[t5]} -O ${STARTDIR}/data/${outname}
  (cd ${STARTDIR}/data; mkdir -p ${OUTDIR}/$tname; cd ${OUTDIR}/$tname; tar xf ${STARTDIR}/data/${outname})
done
