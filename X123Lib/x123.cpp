#include "x123.h"
#include <iostream>
#include <stdio.h>
using namespace std ;


extern "C"{
    X123 *X123_const() {return new X123() ;}
    void X123_acqSpec (X123* x123) {x123->AcquireSpectrum();}
    bool X123_connUSB (X123* x123) { return x123->ConnectUSB();}
    void X123_disconnUSB (X123* x123) { return x123->DisconnectUSB();}
    void X123_clearSpec (X123* x123) {x123->ClearSpectrum();}
    void X123_readCFil (X123* x123, char *cfile) {x123->ReadConfigFile(cfile);}
    void X123_setData (X123* x123, long *specdata) {x123->SetSpecData (specdata);}
    void X123_setSpecFile (X123* x123, char *cfile) {x123->SetSpectrumFile(cfile);}
    void X123_setAcquisitionTime (X123* x123, int secs){x123->SendPresetAcquisitionTime(secs);}
    void X123_startAcquisition (X123* x123){x123->StartAcquisition();}
    int  X123_getCurSecs (X123* x123){ return x123->GetCurSecs() ;}

}
X123::X123()
{
    chdpp = new CConsoleHelper () ;
    haveSpec = false ;
    bRunSpectrumTest = true ;
    bRunConfigurationTest = false ;
    bHaveStatusResponse = false ;
    bHaveConfigFromHW = false ;

    nptsSpec =2048 ;
//    specData = new long [nptsSpec] ;
//    for (int i =0 ; i<nptsSpec; i++) {
//        specData[i] = 0 ;
//    }
    curSecs = 0 ;
    acqSecs = 20 ;
}

X123::~X123 (){
    DisconnectUSB() ;
    delete [] specData ;
}

void X123::SetSpecData (long *sarray){
    specData = sarray ;
}

bool X123::ConnectUSB () {
    cout << endl;
    cout << "Running DPP LibUsb tests from console..." << endl;
    cout << endl;
    cout << "\tConnecting to default LibUsb device..." << endl;
    if (chdpp->LibUsb_Connect_Default_DPP()) {
                    cout << "\t\tLibUsb DPP device connected." << endl;
                    cout << "\t\tLibUsb DPP devices present: "  << chdpp->LibUsb_NumDevices << endl;
                    haveSpec = true ;

    } else {
                    cout << "\t\tLibUsb DPP device not connected." << endl;
                    cout << "\t\tNo LibUsb DPP device present." << endl;
                    haveSpec = false ;

    }

    return (haveSpec) ;
}

void X123::GetDppStatus () {
    if (chdpp->LibUsb_isConnected) { // send and receive status
            cout << endl;
            cout << "\tRequesting Status..." << endl;
            if (chdpp->LibUsb_SendCommand(XMTPT_SEND_STATUS)) {	// request status
                cout << "\t\tStatus sent." << endl;
                cout << "\t\tReceiving status..." << endl;
                if (chdpp->LibUsb_ReceiveData()) {
                    cout << "\t\t\tStatus received..." << endl;
                    cout << chdpp->DppStatusString << endl;
                    bRunSpectrumTest = true;
                    bHaveStatusResponse = true;
                    bRunConfigurationTest = true;
                } else {
                    cout << "\t\tError receiving status." << endl;
                }
            } else {
                cout << "\t\tError sending status." << endl;
            }
        }
        //this->SendPresetAcquisitionTime(20) ;
}


void X123::DisconnectUSB () {

    if (chdpp->LibUsb_isConnected) { // send and receive status
            cout << endl;
            cout << "\tClosing connection to default LibUsb device..." << endl;
            chdpp->LibUsb_Close_Connection();
            cout << "\t\tDPP device connection closed." << endl;
    }

    return ;
}

bool X123::ClearSpectrum () {


    cout << "\tRunning spectrum test..." << endl;
    cout << "\t\tDisabling MCA for spectrum data/status clear." << endl;
    chdpp->LibUsb_SendCommand(XMTPT_DISABLE_MCA_MCS);
    Sleep(1000);
    cout << "\t\tClearing spectrum data/status." << endl;
    chdpp->LibUsb_SendCommand(XMTPT_SEND_CLEAR_SPECTRUM_STATUS);
    Sleep(1000);
    cout << "\t\tEnabling MCA for spectrum data acquisition with status ." << endl;
    return (true) ;
}


bool X123::ReadConfigFile (char *cfile)  {
    FILE *cf = fopen (cfile,"r") ;
    if (cf==NULL) {
        cout << "Could not find config file : " << cfile<<endl ;
        fclose (cf) ;
        return false ;
    }
    fclose (cf) ;
    std::string strCfg ;
    strCfg = chdpp->SndCmd.GetDP5CfgStr (cfile) ;
    cout << "\t\t\tConfiguration Length: " << (unsigned int)strCfg.length() << endl;
    cout << "\t================================================================" << endl;
    cout << strCfg << endl;
    cout << "\t================================================================" << endl;
    return true ;
}

bool X123::SendPresetAcquisitionTime(int sec)
{
    acqSecs = sec ;
    CONFIG_OPTIONS CfgOptions;
    char str[20] ;

    sprintf (str,"PRET=%d;", sec) ;
    string strPRET (str) ;

    cout << "\tSetting Preset Acquisition Time..." << strPRET << endl;
    chdpp->CreateConfigOptions(&CfgOptions, "", chdpp->DP5Stat, false);
    CfgOptions.HwCfgDP5Out = strPRET ;
    // send PresetAcquisitionTime string, bypass any filters, read back the mode and settings
    if (chdpp->LibUsb_SendCommand_Config(XMTPT_SEND_CONFIG_PACKET_EX, CfgOptions)) {
        ReadDppConfigurationFromHardware(false);	// read setting back
        DisplayPresets();
        return true ;
        // display new presets
    } else {
        cout << "\t\tPreset Acquisition Time NOT SET" << strPRET << endl;
        return false ;
    }
}

// Clears spectrum data and starts acquisition
void X123::StartAcquisition(){
    int MaxMCA = acqSecs / 2 + 1;
    int count = 0 ;
    bool bDisableMCA;

    curSecs = 0 ;
    //bRunSpectrumTest = false;		// disable test
    if (bRunSpectrumTest) {
        cout << "\tRunning spectrum test..." << endl;
        cout << "\t\tDisabling MCA for spectrum data/status clear." << endl;
        chdpp->LibUsb_SendCommand(XMTPT_DISABLE_MCA_MCS);
        Sleep(1000);
        cout << "\t\tClearing spectrum data/status." << endl;
        chdpp->LibUsb_SendCommand(XMTPT_SEND_CLEAR_SPECTRUM_STATUS);
        Sleep(1000);
        cout << "\t\tEnabling MCA for spectrum data acquisition with status ." << endl;
        chdpp->LibUsb_SendCommand(XMTPT_ENABLE_MCA_MCS);
        Sleep(1000);
        for(int idxSpectrum=0;idxSpectrum<MaxMCA;idxSpectrum++) {
            //cout << "\t\tAcquiring spectrum data set " << (idxSpectrum+1) << " of " << MaxMCA << endl;
            if (chdpp->LibUsb_SendCommand(XMTPT_SEND_SPECTRUM_STATUS)) {	// request spectrum+status
                if (chdpp->LibUsb_ReceiveData()) {
                        bDisableMCA = true;				// we are aquiring data, disable mca when done
                        //system(CLEAR_TERM);
                        //chdpp->ConsoleGraph(chdpp->DP5Proto.SPECTRUM.DATA,chdpp->DP5Proto.SPECTRUM.CHANNELS,true,chdpp->DppStatusString);
                        for (int i=0; i<nptsSpec; i++){
                            specData[i] = chdpp->DP5Proto.SPECTRUM.DATA[i] ;
                        }
						
                        Sleep(1990);
                        curSecs += 2 ;

                }
            }else {
                    cout << "\t\tProblem acquiring spectrum." << endl;
                    break;
                }
            }
            // now disable MCA if we received data
            if (bDisableMCA) {
                ////system("Pause");
                //cout << "\t\tSpectrum acquisition with status done. Disabling MCA." << endl;
                chdpp->LibUsb_SendCommand(XMTPT_DISABLE_MCA_MCS);
                Sleep(1000);
            }
        }


    // Saving spectrum file
    SaveSpectrumFile() ;
}


void X123::AcquireSpectrum() {


    this->StartAcquisition () ;
    // Saving spectrum file
    SaveSpectrumFile() ;

}

void X123::DisplayPresets(){
    if (bHaveConfigFromHW) {
        cout << "\t\t\tPreset Mode: " << chdpp->strPresetCmd << endl;
        cout << "\t\t\tPreset Settings: " << chdpp->strPresetVal << endl;
    }
}

void X123::ReadDppConfigurationFromHardware(bool bDisplayCfg) {
    CONFIG_OPTIONS CfgOptions;
    if (bHaveStatusResponse && bRunConfigurationTest) {
            //test configuration functions
            // Set options for XMTPT_FULL_READ_CONFIG_PACKET
            chdpp->CreateConfigOptions(&CfgOptions, "", chdpp->DP5Stat, false);
            cout << endl;
            cout << "\tRequesting Full Configuration..." << endl;
            chdpp->ClearConfigReadFormatFlags();	// clear all flags, set flags only for specific readback properties
            //chdpp->DisplayCfg = false;	// DisplayCfg format overrides general readback format
            chdpp->CfgReadBack = true;	// requesting general readback format
            if (chdpp->LibUsb_SendCommand_Config(XMTPT_FULL_READ_CONFIG_PACKET, CfgOptions)) {	// request full configuration
                if (chdpp->LibUsb_ReceiveData()) {
                    if (chdpp->HwCfgReady) {		// config is ready
                        bHaveConfigFromHW = true;
                        if (bDisplayCfg) {
                            cout << "\t\t\tConfiguration Length: " << (unsigned int)chdpp->HwCfgDP5.length() << endl;
                            cout << "\t================================================================" << endl;
                            cout << chdpp->HwCfgDP5 << endl;
                            cout << "\t================================================================" << endl;
                            cout << "\t\t\tScroll up to see configuration settings." << endl;
                            cout << "\t================================================================" << endl;
                        } else {
                            cout << "\t\tFull configuration received." << endl;
                        }
                    }
                }
            }
    }


}

void X123::SetSpectrumFile (char *ifile) {
    chdpp->SetSpectrumFile (ifile) ;
}

// Saving spectrum file
void X123::SaveSpectrumFile()
{
    string strSpectrum;											// holds final spectrum file
    chdpp->sfInfo.strSpectrumStatus = chdpp->DppStatusString;		// save last status after acquisition
    chdpp->sfInfo.m_iNumChan = chdpp->mcaCH;						// number channels in spectrum
    chdpp->sfInfo.SerialNumber = chdpp->DP5Stat.m_DP5_Status.SerialNumber;	// dpp serial number
    chdpp->sfInfo.strDescription = "Amptek Spectrum File";					// description
    chdpp->sfInfo.strTag = "TestTag";										// tag
    // create spectrum file, save file to string
    strSpectrum = chdpp->CreateMCAData(chdpp->DP5Proto.SPECTRUM.DATA,chdpp->sfInfo,chdpp->DP5Stat.m_DP5_Status);
    chdpp->SaveSpectrumStringToFile(strSpectrum);	// save spectrum file string to file
}


int X123::GetCurSecs () {
    return this->curSecs ;
}
