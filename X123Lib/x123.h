#ifndef X123_H
#define X123_H

#include "ConsoleHelper.h"

class X123
{
public:
    explicit X123();
    ~X123 () ;
    CConsoleHelper *chdpp ;
    bool ConnectUSB() ;
    void GetDppStatus () ;
    bool SendPresetAcquisitionTime(int) ;
    void DisconnectUSB() ;
    bool readConfigFile () ;
    void AcquireSpectrum () ;
    void StartAcquisition() ;
    bool ClearSpectrum () ;
    // Saving spectrum file
    void SaveSpectrumFile() ;
    void SetSpectrumFile (char *) ;
    void SetSpecData (int *sarray) ;

    bool ReadConfigFile(char *) ;
    void ReadDppConfigurationFromHardware(bool);
    void DisplayPresets () ;
    bool haveSpec ;
	int	GetCurSecs() ;
    int curSecs, acqSecs ;
    int nptsSpec ;
    int *specData ;

protected :
    bool bRunSpectrumTest, bRunConfigurationTest ;
    bool bHaveStatusResponse, bHaveConfigFromHW ;


    
};

#endif // X123_H
