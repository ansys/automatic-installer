# {} left for formatting to insert product key
uninstall_iss = """[InstallShield Silent]
Version=v7.00
File=Response File
[File Transfer]
OverwrittenReadOnly=NoToAll
[{}-DlgOrder]
Dlg0={}-MessageBox-0
Count=2
Dlg1={}-SdFinish-0
[{}-MessageBox-0]
Result=6
[{}-SdFinish-0]
Result=1
bOpt1=0
bOpt2=0"""