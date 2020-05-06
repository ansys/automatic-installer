import textwrap
# {{{0}}} left for formatting to insert product key
uninstall_iss = textwrap.dedent("""\
                                    [InstallShield Silent]
                                    Version={1}
                                    File=Response File
                                    [File Transfer]
                                    OverwrittenReadOnly=NoToAll
                                    [{{{0}}}-DlgOrder]
                                    Dlg0={{{0}}}-MessageBox-0
                                    Count=2
                                    Dlg1={{{0}}}-SdFinish-0
                                    [{{{0}}}-MessageBox-0]
                                    Result=6
                                    [{{{0}}}-SdFinish-0]
                                    Result=1
                                    bOpt1=0
                                    bOpt2=0
                                """)


# format options: 0-GUID, 1-install dir, 2-temp dir, 3-integrate WB, 4-install shield version
install_iss = textwrap.dedent("""\
                                [InstallShield Silent]
                                Version={4}
                                File=Response File
                                
                                [File Transfer]
                                OverwrittenReadOnly=NoToAll
                                
                                [{{{0}}}-DlgOrder]
                                Dlg0={{{0}}}-SdWelcome-0
                                Count=10
                                Dlg1={{{0}}}-SdLicense-0
                                Dlg2={{{0}}}-SdAskDestPath-0
                                Dlg3={{{0}}}-DLG_ASKTEMPDIROPTION-0
                                Dlg4={{{0}}}-DLG_ASKLIBRARYOPTION-0
                                Dlg5={{{0}}}-DLG_INTEGRATEWITHWB-0
                                Dlg6={{{0}}}-DLG_ASKLICENSEOPTION-0
                                Dlg7={{{0}}}-DLG_ASKSERVERNAMES-0
                                Dlg8={{{0}}}-SdStartCopy-0
                                Dlg9={{{0}}}-SdFinish-0
                                
                                [{{{0}}}-SdWelcome-0]
                                Result=1
                                
                                [{{{0}}}-SdLicense-0]
                                Result=1
                                
                                [{{{0}}}-SdAskDestPath-0]
                                szDir={1}
                                Result=1
                                
                                [{{{0}}}-DLG_ASKTEMPDIROPTION-0]
                                sTempPath={2}
                                bChangeAccess=1
                                Result=1
                                
                                [{{{0}}}-DLG_ASKLIBRARYOPTION-0]
                                nUseExistingLib=0
                                sLibPath=<If using existing libraries, enter the path to the Common Libraries installation here and set nUseExistingLib to 1.  Else, do not edit this line.>
                                Result=1
                     
                                [{{{0}}}-DLG_INTEGRATEWITHWB-0]
                                l3_IntegrateWithWB={3}
                                DlgRetValue=1
                                
                                [{{{0}}}-SdStartCopy-0]
                                Result=1
                                                                
                                [{{{0}}}-SdFinish-0]
                                Result=1
                                bOpt1=0
                                bOpt2=0              
                            """)

existing_server = textwrap.dedent("""
                                    [{{{0}}}-DLG_ASKLICENSEOPTION-0]
                                    nLicenseOption=3
                                    Result=1
                                  """)

new_server = textwrap.dedent("""
                                [{{{0}}}-DLG_ASKLICENSEOPTION-0]
                                nLicenseOption=2
                                Result=1
                                
                                [{{{0}}}-DLG_ASKSERVERNAMES-0]
                                nServerCount=3
                                sServer1=127.0.0.1
                                sServer2=OTTLICENSE5
                                sServer3=PITRH6LICSRV1
                                bSpecifyTCPPort=1
                                sTCPPortNumber=1055
                                Result=1
                             """)
