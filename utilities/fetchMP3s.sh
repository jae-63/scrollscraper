#!/bin/bash
declare -A newmap

# https://drive.google.com/file/d/13AR-eT3WrQSZ7noO9b6GEiqqXL8a5awz/view?usp=sharing
newmap[t1]="13AR-eT3WrQSZ7noO9b6GEiqqXL8a5awz"
# https://drive.google.com/file/d/1zOn02n4DIySBBdYyr5RXKRjZzLe8UngI/view?usp=sharing
newmap[t2]="1zOn02n4DIySBBdYyr5RXKRjZzLe8UngI"
# https://drive.google.com/file/d/1ditZtFKx_ti6I7SN1_hQxIHecx0EkaIA/view?usp=sharing
newmap[t3]="1ditZtFKx_ti6I7SN1_hQxIHecx0EkaIA"
# https://drive.google.com/file/d/1fyv3a7eIhzB7zGDleXp5yDzoS51YS4GL/view?usp=sharing
newmap[t4]="1fyv3a7eIhzB7zGDleXp5yDzoS51YS4GL"
# https://drive.google.com/file/d/1q4RMYvOBm_t1AeQ_r6tpjMweMu4Cf_yx/view?usp=sharing
newmap[t5]="1q4RMYvOBm_t1AeQ_r6tpjMweMu4Cf_yx"

OUTDIR=/ort_mp3s
if [ -z "$IS_DOCKER" ]; then
    OUTDIR=ORT_MP3s.recoded
fi

STARTDIR=$(pwd)
mkdir -p $STARTDIR/data
#gdown https://drive.google.com/uc?id=${newmap[t5]}
for tname in t1 t2 t3 t4 t5; do
  outname="ORT_MP3s.recoded.${tname}.tgz"
  gdown --id ${newmap[$tname]} -O ${STARTDIR}/data/${outname}
  (cd ${STARTDIR}/data; mkdir -p ${OUTDIR}/$tname; cd ${OUTDIR}/$tname; tar xzf ${STARTDIR}/data/${outname})
done
