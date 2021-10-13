[InstallShield Silent]
Version=v7.00
File=Response File

[File Transfer]
OverwrittenReadOnly=NoToAll

[{22139510-d048-4650-9db9-582ee8ede17b}-DlgOrder]
Dlg0={22139510-d048-4650-9db9-582ee8ede17b}-SdWelcome-0
Count=10
Dlg1={22139510-d048-4650-9db9-582ee8ede17b}-SdLicense-0
Dlg2={22139510-d048-4650-9db9-582ee8ede17b}-SdAskDestPath-0
Dlg3={22139510-d048-4650-9db9-582ee8ede17b}-DLG_ASKTEMPDIROPTION-0
Dlg4={22139510-d048-4650-9db9-582ee8ede17b}-DLG_ASKLIBRARYOPTION-0
Dlg5={22139510-d048-4650-9db9-582ee8ede17b}-DLG_INTEGRATEWITHWB-0
Dlg6={22139510-d048-4650-9db9-582ee8ede17b}-DLG_ASKLICENSEOPTION-0
Dlg7={22139510-d048-4650-9db9-582ee8ede17b}-DLG_ASKSERVERNAMES-0
Dlg8={22139510-d048-4650-9db9-582ee8ede17b}-SdStartCopy-0
Dlg9={22139510-d048-4650-9db9-582ee8ede17b}-SdFinish-0

[{22139510-d048-4650-9db9-582ee8ede17b}-SdWelcome-0]
Result=1

[{22139510-d048-4650-9db9-582ee8ede17b}-SdLicense-0]
Result=1

[{22139510-d048-4650-9db9-582ee8ede17b}-SdAskDestPath-0]
szDir=C:\Program Files\AnsysEM
Result=1

[{22139510-d048-4650-9db9-582ee8ede17b}-DLG_ASKTEMPDIROPTION-0]
sTempPath=D:\Temp
bChangeAccess=1
Result=1

[{22139510-d048-4650-9db9-582ee8ede17b}-DLG_ASKLIBRARYOPTION-0]
nUseExistingLib=0
sLibPath=<If using existing libraries, enter the path to the Common Libraries installation here and set nUseExistingLib to 1.  Else, do not edit this line.>
Result=1

[{22139510-d048-4650-9db9-582ee8ede17b}-DLG_INTEGRATEWITHWB-0]
l3_IntegrateWithWB=0
DlgRetValue=1

!!!
!!! BEGIN: License server selection
!!! Recommendation: Use either license option 1 or 2.  Avoid option 3
!!! because it only works on machines that already have ANSYS software installed.
!!! nLicenseOption=1 => "I have a new license file"
!!! nLicenseOption=2 => "I want to specify a license server"
!!!
!!! You may only use one of the below options.  If you enable both,
!!! the silent installation will fail with error code -3.
!!!

!!! BEGIN OPTION 1 (disabled by default): Uncomment below to enable license option 1

![{22139510-d048-4650-9db9-582ee8ede17b}-DLG_ASKLICENSEOPTION-0]
!nLicenseOption=1
!Result=1

![{22139510-d048-4650-9db9-582ee8ede17b}-DLG_ASKLICENSEPATH-0]
!sLicenseDir=c:\temp\AnsysLicenses\
!sLicenseFile=ansoftd-20130701.lic
!Result=1
!!! END OPTION 1 (disabled by default): Uncomment above to enable license option 1

!!! BEGIN OPTION 2 (enabled by default): Comment below to remove license option 2
[{22139510-d048-4650-9db9-582ee8ede17b}-DLG_ASKLICENSEOPTION-0]
nLicenseOption=2
Result=1

[{22139510-d048-4650-9db9-582ee8ede17b}-DLG_ASKSERVERNAMES-0]
! The total number of servers, nServerCount, may be 1 or 3
nServerCount=1
sServer1=PITRH6LICSRV1
sServer2=
sServer3=
bSpecifyTCPPort=1
sTCPPortNumber=1055
Result=1
!!! END OPTION 2 (enabled by default): Comment above to remove license option 2

!!! END: License server selection
!!!

[{22139510-d048-4650-9db9-582ee8ede17b}-SdStartCopy-0]
Result=1

[Application]
Name=ANSYS Electromagnetics
Version=22.1.0
Company=ANSYS, Inc.
Lang=0009

[{22139510-d048-4650-9db9-582ee8ede17b}-SdFinish-0]
Result=1
bOpt1=0
bOpt2=0

