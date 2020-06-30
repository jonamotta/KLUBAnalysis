import argparse
import numpy as np
import pdfkit
import pandas as pd

if __name__ == "__main__" :

	parser = argparse.ArgumentParser(description='Command line parser of plotting options')
	parser.add_argument('--dir', dest='dir', help='single_yields.txt input and yields.txt output folder name', default="./")
	parser.add_argument('--sel', dest='sel', help='selection name', default=None)
	parser.add_argument('--last', dest='last', help='to specify if its the last time we are colling this script inside a list of calls', default=False)
	args = parser.parse_args()

	# READ THE YIELDS CALCULATED FROM THE HISTOS OF THE SINGLE VARIABLES
	with open(args.dir+"/"+args.sel+"/single_yields.txt","r") as single_yields_txt:
		lines = single_yields_txt.readlines()
		with open(args.dir+"/"+args.sel+"/yields_"+args.sel+".txt","w") as yields_txt:
			if "1b1j" in args.sel:
					selName = "1b1j SELECTION"
			if "2b0j" in args.sel:
					selName = "2b0j SELECTION"
			if "0b2j" in args.sel:
					selName = "0b2j CONTROL REGION"
			if "boosted" in args.sel:
					selName = "boosted SELECTION"
			if "loose" in args.sel:
					selName = "VBFloose SELECTION"
			if "baseline" in args.sel:
					selName = "baseline SELECTION"
			yields_txt.write("YIELDS OF THE DIFFERENT PROCESSES FOR THE "+selName+"\n")
			yields_txt.write("-----------------------------------------------------------------\n")

			# THE LIST OF BACKGROUNDS MUST BE THE SAME AS THE ONE WITH THE SAME NAME IN makeFinalPlots.py + the signal
			List_split = ['Signal', 'Others', 'TT', 'DY', 'QCD', 'singleH', 'EWK', 'WJets', 'singleT', 'tripleV',  'doubleV', 'doubleTVV', 'doubleTsingleV', 'ttH', 'ggH', 'VH', 'VBFH']
			single_yield_err = pd.DataFrame(columns=('single_yields','single_errors', 'mean_yield','mean_error'), index=List_split)

			for index in single_yield_err.index.values:
				single_yield_err['single_yields'][index] = []
				single_yield_err['single_errors'][index] = []
				single_yield_err['mean_yield'][index] = 0
				single_yield_err['mean_error'][index] = 0

			for line in lines:
				for index in single_yield_err.index.values:
					if index in line.split(' ')[0]:
						single_yield_err['single_yields'][index].append(float(line.split(' ')[1].replace('\n','')))
						single_yield_err['single_errors'][index].append(float(line.split(' +/- ')[1].replace('\n','')))

			for index in single_yield_err.index.values:
				# CALCULATE MEAN YIELD AND MEAN ERROR (CALCULATED AS SQRT OF SQUARED SUM)
				single_yield_err['mean_yield'][index] = np.mean(single_yield_err['single_yields'][index])
				for i in range(len(single_yield_err['single_errors'][index])):
					single_yield_err['mean_error'][index] = np.sqrt(single_yield_err['single_errors'][index][i] * single_yield_err['single_errors'][index][i])
				# FILL THE FILE
				yields_txt.write(index+": "+str(single_yield_err['mean_yield'][index])+" +/- "+str(single_yield_err['mean_error'][index])+"\n")

			# FILL A SINGLE .txt FILE WITH ALL THE YIELDS
			yields_txt.close()
			yields_txt = open(args.dir+"/"+args.sel+"/yields_"+args.sel+".txt","r")
			complete_yields = open(args.dir+"/yields.txt","a")
			complete_yields.write(yields_txt.read())
			complete_yields.write('\n')

			# WHEN THE SCRIPT IS CALLED FOR THE LAST TIME WE PRODUCE THE FINAL FILES (THE COMPLETE .txt AND THE .html TABLE)
			if args.last:
				# FILL A DATAFRAME WITH ALL THE YIELDS CALCULATED INSIDE THE single_yields.txt FILES
				df = pd.DataFrame(columns=('0b2j_yield', '0b2j_error', '1b1j_yield', '1b1j_error', '2b0j_yield', '2b0j_error', 'boosted_yield', 'boosted_error', 'VBFloose_yield', 'VBFloose_error'), index=List_split)

				sel='s0b2j'
				with open(args.dir+"/"+sel+"/yields_"+sel+".txt","r") as s0b2j_txt:
					lines = s0b2j_txt.readlines()
					for line in lines:
						for index in df.index.values:
							if index in line.split(' ')[0]:
								df['0b2j_yield'][index] = float(line.split(' ')[1].replace('\n',''))
								df['0b2j_error'][index] = float(line.split(' +/- ')[1].replace('\n',''))

				if 'Mcut' in args.sel:
					sel='s1b1jresolvedMcut'
				else:
					sel='s1b1jresolved'
				with open(args.dir+"/"+sel+"/yields_"+sel+".txt","r") as s1b1j_txt:
					lines = s1b1j_txt.readlines()
					for line in lines:
						for index in df.index.values:
							if index in line.split(' ')[0]:
								df['1b1j_yield'][index] = float(line.split(' ')[1].replace('\n',''))
								df['1b1j_error'][index] = float(line.split(' +/- ')[1].replace('\n',''))

				if 'Mcut' in args.sel:
					sel='s2b0jresolvedMcut'
				else:
					sel='s2b0jresolved'
				with open(args.dir+"/"+sel+"/yields_"+sel+".txt","r") as s2b0j_txt:
					lines = s2b0j_txt.readlines()
					for line in lines:
						for index in df.index.values:
							if index in line.split(' ')[0]:
								df['2b0j_yield'][index] = float(line.split(' ')[1].replace('\n',''))
								df['2b0j_error'][index] = float(line.split(' +/- ')[1].replace('\n',''))

				if 'Mcut' in args.sel:
					sel='sboostedLLMcut'
				else:
					sel='sboostedLL'
				with open(args.dir+"/"+sel+"/yields_"+sel+".txt","r") as sboosted_txt:
					lines = sboosted_txt.readlines()
					for line in lines:
						for index in df.index.values:
							if index in line.split(' ')[0]:
								df['boosted_yield'][index] = float(line.split(' ')[1].replace('\n',''))
								df['boosted_error'][index] = float(line.split(' +/- ')[1].replace('\n',''))

				if 'Mcut' in args.sel:
					sel='VBFlooseMcut'
				else:
					sel='VBFloose'
				with open(args.dir+"/"+sel+"/yields_"+sel+".txt","r") as s1b1j_txt:
					lines = s1b1j_txt.readlines()
					for line in lines:
						for index in df.index.values:
							if index in line.split(' ')[0]:
								df['VBFloose_yield'][index] = float(line.split(' ')[1].replace('\n',''))
								df['VBFloose_error'][index] = float(line.split(' +/- ')[1].replace('\n',''))

				# VERIFY THE MAGNITUDE OF THE DIFFERENT BKG PROCESSES SO THAT Others IS NOT BIGGER THAN THE MAIN BKGS
				# IF Others BECOMES COMPARABLE WITH THE OTHER LARGEST BKG THEN WE EXPAND IT IN ITS MAIN CONTRIBUTIONS
				for column in df.columns.values:
					if 'yield' in column:
						if (df[column]['TT'] >= df[column]['DY']) and (df[column]['TT'] >= df[column]['QCD']):
						   largest_bkg = df[column]['TT']
						elif (df[column]['DY'] >= df[column]['TT']) and (df[column]['DY'] >= df[column]['QCD']):
						   largest_bkg = df[column]['DY']
						else:
						   largest_bkg = df[column]['QCD']

						if df[column]['Others']/largest_bkg > 0.1:
							df[column]['Others'] = df[column]['tripleV'] + df[column]['doubleV'] + df[column]['doubleTVV'] + df[column]['doubleTsingleV'] + df[column]['WJets']
							# TO BE CONSERVATIVE WE SIMPLY SUM THE ERRORS INSTEAD OF SUMMING THEM IN QUADRATURE
							df[column.replace('yield','error')]['Others'] = df[column.replace('yield','error')]['tripleV'] + df[column.replace('yield','error')]['doubleV'] + df[column.replace('yield','error')]['doubleTVV'] + df[column.replace('yield','error')]['doubleTsingleV'] + df[column.replace('yield','error')]['WJets']
						else:
							for i in ['EWK', 'singleT']:
								df[column][i] = '---'
								df[column.replace('yield','error')][i] = '---'


				# CREATE AND FILL THE A DATAFRAME TO BE USED FOR THE PRINTING OF THE COMPLETE .html TABLE
				df_print = pd.DataFrame(columns=('0b2j', '1b1j', '2b0j', 'boosted', 'VBFloose'), index=List_split)
				for column in df.columns.values:
					if 'yield' in column:
						for index in df.index.values:
							if df[column][index] != '---':
								# correct for the normalization to 1pb of the signal (SM xs = 31.05fb)
								if 'Signal' in index:
									df_print[column.replace('_yield','')][index] = str(round(float(df[column][index])*31.05/1000.,2))+' +/- '+str(round(float(df[column.replace('yield','error')][index])*31.05/1000.,2))
								else:
									df_print[column.replace('_yield','')][index] = str(round(float(df[column][index]),1))+' +/- '+str(round(float(df[column.replace('yield','error')][index]),1))
								if (abs(float(df_print[column.replace('_yield','')][index].split(' ')[0]))) == 0.0:
									df_print[column.replace('_yield','')][index] = 'negligible'
							else:
								df_print[column.replace('_yield','')][index] = '---'

				# CREATE AND FILL THE A DATAFRAME TO BE USED FOR THE PRINTING OF THE SINGLE H YIELDS .html TABLE
				singleH_df = pd.DataFrame(columns=('0b2j', '1b1j', '2b0j', 'boosted', 'VBFloose'), index=['ttH', 'ggH', 'VH', 'VBFH'])
				for column in df.columns.values:
					if 'yield' in column:
						for index in ['ttH', 'ggH', 'VH', 'VBFH']:
							singleH_df[column.replace('_yield','')][index] = str(round(float(df[column][index]),2))+' +/- '+str(round(float(df[column.replace('yield','error')][index]),2))

				html_df = df_print.drop(index=['tripleV',  'doubleV', 'doubleTVV', 'doubleTsingleV', 'WJets', 'ttH', 'ggH', 'VH', 'VBFH'])
				html_df.rename(columns={'0b2j':'0b2j CR', '1b1j':'1b1j resolved', '2b0j':'2b0j resolved'}, inplace=True)
				singleH_df.rename(columns={'0b2j':'0b2j CR', '1b1j':'1b1j resolved', '2b0j':'2b0j resolved'}, inplace=True)
				html_df.to_html(args.dir+'/yields.html')
				singleH_df.to_html(args.dir+'/singleH_yields.html')
				# FOR SOME REASON pdfkit DOES NOT WORK -> THE TABLE IS ANYWAYS IN THE html FILE
				#pdfkit.from_file(args.dir+'/yields.html',args.dir+'yields.pdf')
