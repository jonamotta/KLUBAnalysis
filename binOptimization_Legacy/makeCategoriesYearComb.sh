#!/bin/bash
export TAG="combined"
export CF="$CMSSW_BASE/src/KLUBAnalysis/binOptimization_Legacy/VBFcombined/"
export LEPTONS="ETau MuTau TauTau "
export SELECTIONS="VBFloose"
export YEARS="2016 2017 2018"
export VARIABLE="DNNoutSM_kl_1"



# ggHH_bbtt IS THE OLD NAME FOR SM PRODUCTION OF THE HH PAIR
export NAMESAMPLE="ggHH_bbtt"
if [ "${SELECTIONS}" == "VBFloose" ]
		then
		export NAMESAMPLE="VBFHH_bbtt"
fi

export RESONANT=$2

echo $VARIABLE
echo $YEARS
echo $LEPTONS
echo $SELECTIONS
echo ""

export QUANTILES="0.025 0.16 0.5 0.84 0.975 -1.0"


# CREATE ALL THE CARDS -> SELECTIONS x CHANNELS (AT MOST 13 CASES = 3 CHANNELS x 5 SELECTIONS - 2 NON EXISTING COMBINATIONS)
for s in $SELECTIONS
do
		for c in $LEPTONS
		do
				for y in $YEARS
				do
						if [ "${y}" == "2017" ]
						then
								if [[ "${c}" == "MuTau" ]]
								then
										continue
								fi
						fi
						python chcardMaker.py --filename ${CF}/analyzedOutPlotter_${c}_${y}.root --dir "_${y}" --channel ${c} --binbybin --selection ${s} ${RESONANT} --shape 1 --theory --path ${CF} --year ${y} --var ${VARIABLE} --lambda ${NAMESAMPLE}"11" --combination "yes"

				done
		done
done

echo ""
echo "ALL CARDS CREATED"
echo "STARTING COMBINATION AND SINGLE LIMIT CALCULATION"
echo ""

mkdir ${CF}/cards_${TAG}_${VARIABLE}
for s in $SELECTIONS
do
		for c in $LEPTONS
		do
				for y in $YEARS
				do
						if [ "${y}" == "2017" ]
						then
								if [[ "${c}" == "MuTau"  ]]
								then
										continue
								fi
						fi
						cp ${CF}/cards_${c}_${y}/${NAMESAMPLE}11${s}${VARIABLE}/* ${CF}/cards_${TAG}_${VARIABLE}/
				done
		done
done

cd ${CF}/cards_${TAG}_${VARIABLE}
if [ "${SELECTIONS}" == "VBFloose" ]
then
		combineCards.py -S hh_*_C4_L${NAMESAMPLE}11_13Te*.txt  >> comb.txt
else
		combineCards.py -S hh_*_C1_L${NAMESAMPLE}11_13Te*.txt hh_*_C2_L${NAMESAMPLE}11_13Te*.txt hh_*_C3_L${NAMESAMPLE}11_13Te*.txt >> comb.txt
fi
text2workspace.py -m "11" comb.txt -o comb.root ;
ln -ns /home/llr/cms/motta/CMSSW_10_2_16/src/KLUBAnalysis/binOptimization_Legacy/prepareHybrid.py .
ln -ns /home/llr/cms/motta/CMSSW_10_2_16/src/KLUBAnalysis/binOptimization_Legacy/prepareGOF.py .
ln -ns /home/llr/cms/motta/CMSSW_10_2_16/src/KLUBAnalysis/binOptimization_Legacy/prepareAsymptotic.py .
ln -ns /home/llr/cms/motta/CMSSW_10_2_16/src/KLUBAnalysis/binOptimization_Legacy/prepareImpacts.py .
python prepareAsymptotic.py -m "11" -n ${NAMESAMPLE}
