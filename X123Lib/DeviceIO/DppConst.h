
#pragma once

typedef enum ACQ_DEVICE_TYPE {
	/// MCA8000A uses PMCA COM API not supported in this application.
    devtypeMCA8000A,
	/// DP4 uses DPPAPI and DPP legacy protocol not supported in this application.
    devtypeDP4,
	/// PX4 uses DPPAPI and DPP legacy protocol not supported in this application.
    devtypePX4,
	/// DP5 (FW5) with DP4 emulation uses DPPAPI and DPP legacy protocol not supported in this application.
	devtypeDP4EMUL,
	/// DP5 (FW5) with Px4 emulation uses DPPAPI and DPP legacy protocol not supported in this application.
	devtypePX4EMUL,
	/// DP5 uses DPP new (this) protocol is supported in this application
	devtypeDP5,
	/// PX5 uses DPP new (this) protocol is supported in this application
	devtypePX5,
	/// DP5G uses DPP new (this) protocol is supported in this application
	devtypeDP5G,
	/// MCA8000D uses DPP new (this) protocol is supported in this application
	devtypeMCA8000D,
	/// TB5 uses DPP new (this) protocol is supported in this application ==3
	devtypeTB5
} acqDeviceType;

typedef enum DP5_DPP_TYPES 
{
	/// DP5 uses DPP new (this) protocol is supported in this application ==0
	dppDP5,
	/// PX5 uses DPP new (this) protocol is supported in this application ==1
	dppPX5,
	/// DP5G uses DPP new (this) protocol is supported in this application ==2
	dppDP5G,
	/// MCA8000D uses DPP new (this) protocol is supported in this application ==3
	dppMCA8000D,
	/// TB5 uses DPP new (this) protocol is supported in this application ==3
	dppTB5
} dp5DppTypes;
