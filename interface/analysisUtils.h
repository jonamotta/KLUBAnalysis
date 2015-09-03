#ifndef analysisUtils_h
#define analysisUtils_h

#include <cstdlib>
#include <iostream>
#include <iomanip>
#include <vector>
#include <string>
#include <map>
#include <unordered_map>
#include <algorithm>
#include <fstream>

#include "RooHist.h"
#include "RooCurve.h"

#include "TH1F.h"
#include "TH2F.h"
#include "THStack.h"
#include "TFile.h"
#include "TMath.h"
#include "TTreeFormula.h"

#include "utils.h"
#include "histoUtils.h"
#include "ConfigParser.h"
#include "HistoManager.h"
#include "plotContainer.h"


vector<pair <TString, TCut> > 
addSelection (vector<pair <TString, TCut> > m_cuts, string cut, string tag) ;

std::pair<int, int> leptonsType (int pairType) ;
/*
0 = muons
1 = electrons
2 = taus
true = is isolated
*/
bool isIsolated (int leptonType, float threshold, float isoDeposits, float pT) ; 

void
addHistos (vector<sample> & samples, HistoManager * manager,
           vector<string> & variablesList,
           vector<pair <TString, TCut> > & selections,
           bool isSignal,
           bool isData = false) ;

counters
fillHistos (vector<sample> & samples, 
            plotContainer & plots,
            vector<string> & variablesList,
            vector<pair <TString, TCut> > & selections,
            float lumi,
            const vector<float> & scale,
            bool isData = false,
            bool isSignal = false) ;


vector<THStack *> 
stackHistos (vector<sample> & samples, HistoManager * manager, 
            vector<string> & variablesList,
            vector<pair <TString, TCut> > & selections,
            const string & tag) ;

#endif