#!/bin/bash
# make cards with all vars/selections

# TAG OF THE OUTPUT FOLDER
export OUTSTRING="test_analysis"
#TAG OF THE INPUT FILE
export INSTRING="test_analysis"
# PATH OF THE INPUT FOLDER
export INPATH="../test_analysis/"
# PATH OF THE OUTPUT FOLDER
export CF="$CMSSW_BASE/src/KLUBAnalysis/combiner2018"

export SELECTIONS="s2b0jresolvedMcut s1b1jresolvedMcut sboostedLLMcut VBFtight VBFloose"

# ggHH_bbtt IS THE OLD NAME FOR SM PRODUCTION OF THE HH PAIR
export NAMESAMPLE="ggHH_bbtt"

export RESONANT=$2
#export LEPTONS=$1
#export LEPTONS="ETau MuTau TauTau"
export LEPTONS="TauTau"

# VALUES OF kLambda ON WHICH THE PROGRAM WILL LOOP WHEN WE NEED TO DO THE kLambda SCAN -> MUST BE THE SAME AS IN chcardMaker.py
klvar=(-20 -15 -10 -8 -6 -4 -3 -2 -1 0.001 1 2 3 2.45 4 5 6 7 8 9 10 11 12 14 16 18 20 25 30)

if [ "${RESONANT}" != "-r" ]
		then
		export VARIABLE=""
		export LAMBDAS=""
		export VARIABLES=""
		# IF WE ARE DOING A SCAN UNCOMMENT THE FOR BELOW AND COMMENT THE FOLLOWING TWO LINES
		#for il in {1..29}
		#do
		#		export LAMBDAS="$LAMBDAS${il}"
		#		export VARIABLES="${VARIABLES}BDToutSM_kl_${klvar[$((il-1))]}"
		#done
		# IF WE ARE NOT DOING A SCAN, BUT WE ARE DOING ONLY THE SM CASE, UNCOMMENT THE FOLLOWING TWO LINES AND COMMENT THE FOR ABOVE
		export LAMBDAS="11"
		export VARIABLES="BDToutSM_kl_1"
fi

export QUANTILES="0.025 0.16 0.5 0.84 0.975 -1.0"

echo $VARIABLES
arrVARIABLES=($VARIABLES)
echo ""

# CREATE ALL THE CARDS -> SELECTIONS x CHANNELS (AT MOST 13 CASES = 3 CHANNELS x 5 SELECTIONS - 2 NON EXISTING COMBINATIONS)
for ibase in $SELECTIONS
do
		for c in $LEPTONS
		do
				export BASE="$ibase"
				# VBFtight SELECTION DOES NOT EXIST FOR THE MuTau/ETau CHANNEL -> SKYP IT, THE CARD DOES NOT EXIST FOR THIS
				if [ "${c}" == "MuTau" ]
				then
						if [[ "${ibase}" == *"VBFtight"*  ]]
						then
								continue
						fi
				fi
				if [ "${c}" == "ETau" ]
				then
						if [[ "${ibase}" == *"VBFtight"*  ]]
						then
								continue
						fi
				fi
				python chcardMaker.py -f ${INPATH}analyzedOutPlotter_${INSTRING}.root -o "_${OUTSTRING}" -c ${c} -y -s ${BASE} ${RESONANT} -u 1 -t
		done
done
echo " "
echo "ALL CARDS CREATED"
echo "STARTING SINGLE CHANNEL LIMITS CALCULATION"
echo ""
for i in $LAMBDAS
do
		# MAKE LIMIT FOR EACH CHANNEL AND EACH SELECTION [9 x mass points]
		for ibase in $SELECTIONS
		do
				for c in $LEPTONS
				do
						export BASE="$ibase"
						# VBFtight SELECTION DOES NOT EXIST FOR THE MuTau/ETau CHANNEL -> SKYP IT, THE CARD DOES NOT EXIST FOR THIS
						if [ "${c}" == "MuTau" ]
						then
								export chanNum="2"
								echo "${c} ${chanNum}"
								if [[ "${ibase}" == *"VBFtight"*  ]]
								then
										continue
								fi
						fi
						if [ "${c}" == "ETau" ]
						then
								export chanNum="1"
								echo "${c} ${chanNum}"
								if [[ "${ibase}" == *"VBFtight"*  ]]
								then
										continue
								fi
						fi
						if [ "${c}" == "TauTau" ]
						then
								export chanNum="3"
								echo "${c} ${chanNum}"
						fi

						echo ${CF}/cards_${c}_$OUTSTRING/${NAMESAMPLE}${i}${BASE}${arrVARIABLES[0]}
						cd ${CF}/cards_${c}_$OUTSTRING/${NAMESAMPLE}${i}${BASE}${arrVARIABLES[0]} #---------------------------- cfr. THIS WITH LINE 78 OF chcardMaker.py TO SEE HOW TO CREATE/CALL CORRECTLY
						pwd
						combineCards.py -S hh_*.txt &> comb.txt
						text2workspace.py comb.txt -m ${i} -o comb.root ;
						ln -ns ../../prepareHybrid.py . # the f option forces to overwrite the link if it already exists
						ln -ns ../../prepareGOF.py .
						ln -ns ../../prepareAsymptotic.py .
						python prepareAsymptotic.py -m ${i} -n ${NAMESAMPLE}$i
						cd ${CF}
				done
		done
done
echo " "
echo "SINGLE CHANNEL LIMITS CALCULATED"
echo "STARTING CARDS COMBINATION AND COMBINED LIMIT CALCULATION"
echo ""
# CATEGORY COMBINATION
for i in $LAMBDAS
do
		cd ${CF}
		mkdir -p cards_Combined_$OUTSTRING/${NAMESAMPLE}${i}${arrVARIABLES[0]}
		pwd
		# MAKE COMBINATION PER CATEGORY [3 x mass point] AND CALCULATE COMBINED LIMITS
		for ibase in $SELECTIONS
		do
				mkdir -p cards_Combined_$OUTSTRING/${NAMESAMPLE}${i}${ibase}${arrVARIABLES[0]}
				for c in $LEPTONS
				do
						export BASE="$ibase"
						if [[ "${c}" != "TauTau" && "${ibase}" == *"VBFtight"* ]]
						then
								continue
						fi

						# access the single channels directories and copy the datacards inside the combined directory
						mkdir -p cards_${c}_$OUTSTRING/${NAMESAMPLE}${i}${arrVARIABLES[0]}
						cp cards_${c}_$OUTSTRING/${NAMESAMPLE}${i}${BASE}${arrVARIABLES[0]}/hh_*.* cards_Combined_$OUTSTRING/${NAMESAMPLE}${i}${ibase}${arrVARIABLES[0]}/.
						cp cards_${c}_$OUTSTRING/${NAMESAMPLE}${i}${BASE}${arrVARIABLES[0]}/hh_*.* cards_Combined_$OUTSTRING/${NAMESAMPLE}${i}${arrVARIABLES[0]}/.
						cp cards_${c}_$OUTSTRING/${NAMESAMPLE}${i}${BASE}${arrVARIABLES[0]}/hh_*.* cards_${c}_$OUTSTRING/${NAMESAMPLE}${i}${arrVARIABLES[0]}/.
				done
				cd cards_Combined_$OUTSTRING/${NAMESAMPLE}${i}${ibase}${arrVARIABLES[0]}
				pwd

				# CATEGORIES:
				# C1 = s1b1jresolvedMcut
				# C2 = s2b0jresolvedMcut
				# C3 = sboostedLLMcut
				# C4 = VBFloose
				# C5 = VBFtight

				# combines per selection (C1, C2, C3, C4, C5)
				if [ -a "hh_3_C1_L${NAMESAMPLE}${i}_13TeV.txt" ]
				then
						combineCards.py -S hh_*_C1_L${NAMESAMPLE}${i}_13Te*.txt  &> comb.txt
				fi
				if [ -a "hh_3_C2_L${NAMESAMPLE}${i}_13TeV.txt" ]
				then
						combineCards.py -S hh_*_C2_L${NAMESAMPLE}${i}_13Te*.txt &> comb.txt
				fi
				if [ -a "hh_3_C3_L${NAMESAMPLE}${i}_13TeV.txt" ]
				then
						combineCards.py -S hh_*_C3_L${NAMESAMPLE}${i}_13Te*.txt &> comb.txt
				fi
				if [ -a "hh_3_C4_L${NAMESAMPLE}${i}_13TeV.txt" ]
				then
						combineCards.py -S hh_*_C4_L${NAMESAMPLE}${i}_13Te*.txt &> comb.txt
				fi
				if [ -a "hh_3_C5_L${NAMESAMPLE}${i}_13TeV.txt" ]
				then
						combineCards.py -S hh_3_C5_L${NAMESAMPLE}${i}_13Te*.txt &> comb.txt
				fi

				text2workspace.py -m ${i} comb.txt -o comb.root ;
				ln -ns ../../prepareHybrid.py . # the f option forces to overwrite the link if it already exists
				ln -ns ../../prepareGOF.py .
				ln -ns ../../prepareAsymptotic.py .
				python prepareAsymptotic.py -m ${i} -n ${NAMESAMPLE}$i
				cd ${CF}
			done

		# MAKE BIG COMPLETE COMBINATION [1 x mass point]
		# access the combined directory and create a single combination of all datacrads of all channels (does this for each mass point)
		cd cards_Combined_$OUTSTRING/${NAMESAMPLE}${i}${arrVARIABLES[0]}
		rm comb.*
		combineCards.py -S hh_*_C1_L${NAMESAMPLE}${i}_13Te*.txt hh_*_C2_L${NAMESAMPLE}${i}_13Te*.txt hh_*_C3_L${NAMESAMPLE}${i}_13Te*.txt hh_*_C4_L${NAMESAMPLE}${i}_13Te*.txt hh_*_C5_L${NAMESAMPLE}${i}_13Te*.txt>> comb.txt
		text2workspace.py -m ${i} comb.txt -o comb.root ;
		ln -ns ../../prepareHybrid.py . # the f option forces to overwrite the link if it already exists
		ln -ns ../../prepareGOF.py .
		ln -ns ../../prepareAsymptotic.py .
		ln -ns ../../prepareImpacts.py .
		python prepareAsymptotic.py -m ${i} -n ${NAMESAMPLE}$i
		cd ${CF}

		# MAKE BIG COMBINATION FOR EACH CHANNEL [3 x mass point]
		# access the single channels directories and create a single combination of all datacards inside the single channel (does this for each mass point)
		for c in $LEPTONS
		do

		cd cards_${c}_$OUTSTRING/${NAMESAMPLE}${i}${arrVARIABLES[0]}
		rm comb.*
		if [[ ${c} == "TauTau" ]]
		then
				combineCards.py -S hh_*_C1_L${NAMESAMPLE}${i}_13Te*.txt hh_*_C2_L${NAMESAMPLE}${i}_13Te*.txt hh_*_C3_L${NAMESAMPLE}${i}_13Te*.txt hh_*_C4_L${NAMESAMPLE}${i}_13Te*.txt hh_*_C5_L${NAMESAMPLE}${i}_13Te*.txt>> comb.txt
		else
				combineCards.py -S hh_*_C1_L${NAMESAMPLE}${i}_13Te*.txt hh_*_C2_L${NAMESAMPLE}${i}_13Te*.txt hh_*_C3_L${NAMESAMPLE}${i}_13Te*.txt hh_*_C4_L${NAMESAMPLE}${i}_13Te*.txt>> comb.txt
		fi

		text2workspace.py -m ${i} comb.txt -o comb.root ;
		ln -ns ../../prepareHybrid.py . # the f option forces to overwrite the link if it already exists
		ln -ns ../../prepareGOF.py .
		ln -ns ../../prepareAsymptotic.py .
		python prepareAsymptotic.py -m ${i} -n ${NAMESAMPLE}$i
		cd ${CF}
		done
done