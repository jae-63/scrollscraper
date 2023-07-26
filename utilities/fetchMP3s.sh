#!/bin/bash
declare -A newmap

# https://drive.google.com/file/d/1u1KTSl_fyKWswqbz4mFK67oyjg9CKN4h/view?usp=sharing
newmap[t1]="1u1KTSl_fyKWswqbz4mFK67oyjg9CKN4h"
# https://drive.google.com/file/d/1EtkS0zvq4yOriIu3AlCwWDFirF3U67YN/view?usp=sharing
newmap[t2]="1EtkS0zvq4yOriIu3AlCwWDFirF3U67YN"
# https://drive.google.com/file/d/1Jm6cwqiX4xQltEtUb41IyXmXj0crVZDS/view?usp=sharing
newmap[t3]="1Jm6cwqiX4xQltEtUb41IyXmXj0crVZDS"
# https://drive.google.com/file/d/1XTX8F3yanKXBoNw7lA7MxWEjX2FlwRhR/view?usp=sharing
newmap[t4]="1XTX8F3yanKXBoNw7lA7MxWEjX2FlwRhR"
# https://drive.google.com/file/d/16Y0bVdiG4qNsjzsNDcOtkxXDsJKX77bS/view?usp=sharing
newmap[t5]="16Y0bVdiG4qNsjzsNDcOtkxXDsJKX77bS"

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
