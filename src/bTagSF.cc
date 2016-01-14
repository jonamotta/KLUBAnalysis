#include "bTagSF.h"
#include "TLorentzVector.h"
#include "TString.h"
#include "TMath.h"

using namespace std;

bTagSF::bTagSF(std::string SFfilename) : 
    
    m_calib("CSVv2", SFfilename.c_str()) ,
    m_reader {
    BTagCalibrationReader(&m_calib , BTagEntry::OP_LOOSE,  "comb", "central"),
    BTagCalibrationReader(&m_calib , BTagEntry::OP_MEDIUM, "comb", "central"),
    BTagCalibrationReader(&m_calib , BTagEntry::OP_TIGHT,  "comb", "central")} ,
    m_reader_up {
    BTagCalibrationReader(&m_calib , BTagEntry::OP_LOOSE,  "comb", "up"),
    BTagCalibrationReader(&m_calib , BTagEntry::OP_MEDIUM, "comb", "up"),
    BTagCalibrationReader(&m_calib , BTagEntry::OP_TIGHT,  "comb", "up")} ,
    m_reader_do {
    BTagCalibrationReader(&m_calib , BTagEntry::OP_LOOSE,  "comb", "down"),
    BTagCalibrationReader(&m_calib , BTagEntry::OP_MEDIUM, "comb", "down"),
    BTagCalibrationReader(&m_calib , BTagEntry::OP_TIGHT,  "comb", "down")}
{
    m_fileEff = 0;
}


bTagSF::bTagSF(std::string SFfilename, std::string effFileName, std::string effHistoTag) :
    
    m_calib("CSVv2", SFfilename.c_str()) ,
    m_reader {
    BTagCalibrationReader(&m_calib , BTagEntry::OP_LOOSE,  "comb", "central"),
    BTagCalibrationReader(&m_calib , BTagEntry::OP_MEDIUM, "comb", "central"),
    BTagCalibrationReader(&m_calib , BTagEntry::OP_TIGHT,  "comb", "central")} ,
    m_reader_up {
    BTagCalibrationReader(&m_calib , BTagEntry::OP_LOOSE,  "comb", "up"),
    BTagCalibrationReader(&m_calib , BTagEntry::OP_MEDIUM, "comb", "up"),
    BTagCalibrationReader(&m_calib , BTagEntry::OP_TIGHT,  "comb", "up")} ,
    m_reader_do {
    BTagCalibrationReader(&m_calib , BTagEntry::OP_LOOSE,  "comb", "down"),
    BTagCalibrationReader(&m_calib , BTagEntry::OP_MEDIUM, "comb", "down"),
    BTagCalibrationReader(&m_calib , BTagEntry::OP_TIGHT,  "comb", "down")}
{
    m_fileEff = new TFile (effFileName.c_str());
 
    TString flavs[3]   = {"b", "c", "udsg"};
    TString chnames[3] = {"MuTau", "EleTau", "TauTau"};
    TString WPnames[3] = {"L", "M", "T"};
 
    for (int iWP = 0; iWP < 3; iWP++)
    {
        for (int flav = 0; flav < 3; flav++)
        {
        for (int channel = 0; channel < 3; channel++)
            {
                TString name = Form("eff_%s_%s_%s", flavs[flav].Data(), WPnames[iWP].Data(), chnames[channel].Data());
                //cout << "Tmps name " << name << endl;
                m_hEff [iWP][flav][channel] = (TH1F*) m_fileEff->Get(name.Data());
                //cout << " --> " << m_hEff [iWP][flav][channel] -> GetName() << endl;
            }
        }
    }
}

bTagSF::~bTagSF()
{
    if (m_fileEff) delete m_fileEff;
}

float bTagSF::getSF (WP wpt, SFsyst syst, int jetFlavor, float pt, float eta)
{
    float SF = 1.0;
    
    BTagEntry::JetFlavor flav;
    if (abs(jetFlavor) == 5) flav = BTagEntry::FLAV_B;
    else if (abs(jetFlavor) == 4) flav = BTagEntry::FLAV_C;
    else flav = BTagEntry::FLAV_UDSG;

    if (syst == central)
        SF = m_reader[(int)wpt].eval(flav, eta, pt);   
    else if (syst == up)
        SF = m_reader_up[(int)wpt].eval(flav, eta, pt);
    
    else if (syst == down)
        SF = m_reader_do[(int)wpt].eval(flav, eta, pt);
    
    // double uncertainty up/down if out of some boundaries
    // FIXME: this is wrong!! one should do : jet_scalefactor_up = 2*(jet_scalefactor_up - jet_scalefactor) + jet_scalefactor; 
    // and not just double the scale
    if (syst != central)
    {
        /*
        if (flav == BTagEntry::FLAV_B || flav == BTagEntry::FLAV_C)
        {
            if (pt < 30.0 || pt > 670.0 ) SF *= 2.0;
        }
        if (flav == BTagEntry::FLAV_UDSG)
        {
            if (pt < 20.0 || pt > 1000.0 ) SF *= 2.0;
        }
        */
        SF *= 1.0;
    }

    return SF;
}


float bTagSF::getEff (WP wpt, int jetFlavor, int channel, float pt, float eta)
{
    int flav;
    if (abs(jetFlavor) == 5) flav = 0;
    else if (abs(jetFlavor) == 4) flav = 1;
    else flav = 2;

    TH1F* h = m_hEff [(int) wpt] [flav] [channel];
    float aEta = TMath::Abs(eta);

    int binglobal = h->FindBin (pt, aEta);
    int binx, biny, binz;
    h->GetBinXYZ (binglobal, binx, biny, binz); // converts to x, y bins
    int nx = h->GetNbinsX();
    int ny = h->GetNbinsY();
    
    // under-overflows
    if (binx < 1) binx = 1;
    if (biny < 1) biny = 1;
    if (binx > nx) binx = nx;
    if (biny > ny) biny = ny;

    /*
    float minPt = h->GetXaxis()->GetBinLowEdge(1);
    float maxPt = h->GetXaxis()->GetBinLowEdge(nx+1);

    float minEta = h->GetYaxis()->GetBinLowEdge(1);
    float maxEta = h->GetYaxis()->GetBinLowEdge(ny+1);
    */

    float eff = h->GetBinContent (binx, biny);

    // protection againts wrongly measured efficiencies (low stat) --> reduce pT bin
    while (eff < 0.00000000001 && binx > 0)
    {
        binx-- ;
        eff = h->GetBinContent (binx, biny);
    }

    return eff;
}

// the collection jets_and_btag in input contain all the final list of jets, already cleaned from PU and leptons
// returns a collection of weights according to the tested WP
vector<float> bTagSF::getEvtWeight (std::vector <std::pair <int, float> >& jets_and_btag, std::vector<float> *jets_px, std::vector<float> *jets_py, std::vector<float> *jets_pz, std::vector<float> *jets_e, std::vector<int> *jets_HadronFlavour, int channel)
{

    vector<float> P_MC   (3, 1.0); // 0 = L, 1 = M, 2 = T
    vector<float> P_Data (3, 1.0); // 0 = L, 1 = M, 2 = T
    
    TLorentzVector vJet (0,0,0,0);
    float WPtag[3] = {0.605, 0.89, 0.97}; // L, M, T
    
    for (unsigned int ijet = 0; ijet < jets_and_btag.size(); ijet++)
    {
        int idx = jets_and_btag.at(ijet).first;
        vJet.SetPxPyPzE (jets_px->at(idx), jets_py->at(idx), jets_pz->at(idx), jets_e->at(idx));
        
        int flav = jets_HadronFlavour->at(idx);
        float SF[3];
        SF[0] = getSF (loose,  central, flav, vJet.Pt(), vJet.Eta());
        SF[1] = getSF (medium, central, flav, vJet.Pt(), vJet.Eta());
        SF[2] = getSF (tight,  central, flav, vJet.Pt(), vJet.Eta());

        float effBTag[3];
        effBTag[0] = getEff (static_cast<WP> (0), flav, channel, vJet.Pt(), vJet.Eta()) ;
        effBTag[1] = getEff (static_cast<WP> (1), flav, channel, vJet.Pt(), vJet.Eta()) ;
        effBTag[2] = getEff (static_cast<WP> (2), flav, channel, vJet.Pt(), vJet.Eta()) ;

        float CSV = jets_and_btag.at(ijet).second;
        bool tagged[3];
        tagged[0] = (CSV > WPtag[0]);
        tagged[1] = (CSV > WPtag[1]);
        tagged[2] = (CSV > WPtag[2]);
        for (int iWP = 0; iWP < 3; iWP++)
        {
            float tmpMC   = P_MC.at(iWP);
            float tmpData = P_Data.at(iWP);

            if (tagged[iWP])
            {
                tmpMC *= effBTag[iWP];  
                tmpData *= effBTag[iWP]*SF[iWP];  
            } 
            else
            {
                tmpMC *= (1. - effBTag[iWP]);  
                tmpData *= (1. - (effBTag[iWP]*SF[iWP]) );  
            }
        
            P_MC.at(iWP)  = tmpMC;
            P_Data.at(iWP) = tmpData;

            // if (iWP == 0) 
            // {
            //     cout << ijet << " pt, eta: " << vJet.Pt() << " " << vJet.Eta() << " jet flav: " << flav << " //// SF= " << SF[0] << " eff= " << effBTag[0] << endl;
            // }
        
        }
    }
    // return ratio
    vector<float> weight (3);
    weight.at(0) = P_Data.at(0) / P_MC.at(0);
    weight.at(1) = P_Data.at(1) / P_MC.at(1);
    weight.at(2) = P_Data.at(2) / P_MC.at(2);
    
    if (weight.at(0) < 0.5) 
    {
        cout << "------ NONONO Null weight!!" << endl;
    }
    //cout << "weights: " << weight.at(0) << " " << weight.at(1) << " " << weight.at(2) << endl;
    return weight;
}


