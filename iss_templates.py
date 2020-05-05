import textwrap
# {0} left for formatting to insert product key
uninstall_iss = textwrap.dedent("""\
                                    [InstallShield Silent]
                                    Version=v7.00
                                    File=Response File
                                    [File Transfer]
                                    OverwrittenReadOnly=NoToAll
                                    [{0}-DlgOrder]
                                    Dlg0={0}-MessageBox-0
                                    Count=2
                                    Dlg1={0}-SdFinish-0
                                    [{0}-MessageBox-0]
                                    Result=6
                                    [{0}-SdFinish-0]
                                    Result=1
                                    bOpt1=0
                                    bOpt2=0
                                """)

