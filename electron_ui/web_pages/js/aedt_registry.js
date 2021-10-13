var os_path = require('path');
var fs = require('fs');
var { remote, ipcRenderer } = require('electron');
var { app, dialog } = remote;

settings_path = os_path.join(app.getPath("appData"), "build_downloader", "default_settings.json");
hpc_options_folder = os_path.join(app.getPath("appData"), "build_downloader", "HPC_Options");

$(document).ready(function() {
    /**
     * Create JQuery DataTables for EDT HPC options file.
     * Update table rows, see tables_setter.js
     */
    hpc_table = $('#hpc-options-table').DataTable( {
        "scrollY": "325px",
        "scrollCollapse": true,
        "paging": false,
        "filter": false,
        "ordering": false,
        "info": false,
        "order": [[ 0, "desc" ]]
    } );
    add_hpc_files_rows();

    if (!fs.existsSync(hpc_options_folder)) fs.mkdirSync(hpc_options_folder);

    set_default_tooltips_aedt_options();
} );


$("#add-file-button").click(
    /**
     * When click on the button to append options => 
     * 1. open Electron dialog with filter for .acf files
     * 2. read user input, might be multiple selection
     * 3. synchronously copy files to settings folder/HPC_options
     * 4. update table rows, see tables_setter.js
     */
    function(){
        dialog.showOpenDialog(remote.getCurrentWindow(), {
                properties: ['openFile', 'multiSelections'],
                filters: [
                    { name: 'HPC Options', extensions: ['acf'] },
                    { name: 'Registry Options', extensions: ['txt'] }
                ]
            }).then(
            result => {
                if (result.canceled == false) {
                    var files_selected = result.filePaths;
                    for (var i in files_selected) {
                        var destination = os_path.join(hpc_options_folder, os_path.basename(result.filePaths[i]));
                        fs.copyFileSync(result.filePaths[i], destination , (err) => {
                          if (err) throw err;
                        });
                    }
                    add_hpc_files_rows();
                }
            }).catch(err => {
                  console.log(err)
                })
    }
);


$('#cancel-button').on('click', function(){
    /**
     * just close window
     */
     ipcRenderer.send('aedt_registry_hide');
});
