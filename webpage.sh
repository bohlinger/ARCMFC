#!/bin/bash

region=$1
echo $1

#YEAR=`date +%Y`
YEAR=2021
#MONTH=`date +%m`
MONTH=05

# Create graph plots based on validation results:

# image files
Imgpath=/lustre/storeB/project/fou/om/waveverification/ARCMFC3/satellites/altimetry/s3a/ValidationFigures/${YEAR}/${MONTH}/
Webpath=/lustre/storeB/project/fou/om/waveverification/ARCMFC3/satellites/altimetry/s3a/WebPage/
mkdir -p ${Webpath}${YEAR}-${MONTH}/
cp ${Imgpath}* ${Webpath}${YEAR}-${MONTH}/.

# Create html document:
Imgpath=${YEAR}-${MONTH}/
Figtempl=ARCMFC3_for_${1}_fig_val_ts
rmseImg=${Figtempl}_rmsd_${YEAR}${MONTH}.png
madImg=${Figtempl}_mad_${YEAR}${MONTH}.png
biasImg=${Figtempl}_bias_${YEAR}${MONTH}.png
corrImg=${Figtempl}_corr_${YEAR}${MONTH}.png
SIImg=${Figtempl}_SI_${YEAR}${MONTH}.png
novImg=${Figtempl}_nov_${YEAR}${MONTH}.png
scatterImg1=ARCMFC3_for_${1}_fig_val_scatter_lt012h_${YEAR}${MONTH}.png
scatterImg2=ARCMFC3_for_${1}_fig_val_scatter_lt036h_${YEAR}${MONTH}.png
scatterImg3=ARCMFC3_for_${1}_fig_val_scatter_lt060h_${YEAR}${MONTH}.png

if [ $1 = "ARCMFC3" ]
  then
    echo "Create index.html for region: " ${1}
    htmlFile=${Webpath}${Imgpath}index.html
else
    echo "Create index.html for region: " ${1}
    htmlFile=${Webpath}${Imgpath}index_${1}.html
fi

bName='Bulletin date: '`date +%Y-%m-%d`
echo $bName

cat head1.html               >  ${htmlFile}
echo '<title>'${bName}'</title>'       >> ${htmlFile}
cat head2.html               >> ${htmlFile}

echo '<h2>Results for '${bName}'</h2>' >> ${htmlFile}

#echo '<table><tr><td>'                 >> ${htmlFile}
#echo 'Time series of root mean square error' >> ${htmlFile}
echo '<img src="'${rmseImg}'">'        >> ${htmlFile}
#echo '</td><td>'                       >> ${htmlFile}
#echo '<br>'                            >> ${htmlFile}
#echo '<img src="'${madImg}'">'         >> ${htmlFile}
echo '<br>'                            >> ${htmlFile}
echo '<img src="'${biasImg}'">'        >> ${htmlFile}
echo '<br>'                            >> ${htmlFile}
echo '<img src="'${corrImg}'">'        >> ${htmlFile}
echo '<br>'                            >> ${htmlFile}
echo '<img src="'${SIImg}'">'          >> ${htmlFile}
echo '<br>'                            >> ${htmlFile}
echo '<img src="'${novImg}'">'         >> ${htmlFile}
echo '<br>'                            >> ${htmlFile}
echo '<img src="'${scatterImg1}'">'    >> ${htmlFile}
echo '<img src="'${scatterImg2}'">'    >> ${htmlFile}
echo '<img src="'${scatterImg3}'">'    >> ${htmlFile}
#echo '</td></tr></table>'              >> ${htmlFile}

echo '<p><small>'                      >> ${htmlFile}
echo 'Generated on '`date`             >> ${htmlFile}
echo '</small></p>'                    >> ${htmlFile}

cat tail.html                >> ${htmlFile}
exit
