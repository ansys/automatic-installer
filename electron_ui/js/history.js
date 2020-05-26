var os_path = require('path');
var fs = require('fs');
const { remote } = require('electron');
const { dialog } = require('electron').remote;

settings_path = os_path.join(process.env.APPDATA, "build_downloader", "default_settings.json");
hpc_options_folder = os_path.join(process.env.APPDATA, "build_downloader", "HPC_Options")

function truncate_path(name, selected_path){
    /**
     * truncates end of the path.
     * name (str): what should be removed
     * selected_path (str): path that user selected. Would be truncated
     */
    let truncated_path = selected_path.slice(0, selected_path.length - name.length - 1);
    answer = dialog.showMessageBoxSync(remote.getCurrentWindow(), {
            type: "question",
            buttons: ["Yes", "No"],
            message: "Path contains '" + name + "', Do you want to use '" + truncated_path + "' instead?"
        }
    )

    if (answer == 0) {
        return truncated_path;
    }
    return selected_path;
}

$(document).ready(function() {
    /**
     * On load of the page set settings from JSON file.
     * Enable tooltips
     * If not directory with HPC options => create one
     */
    if (fs.existsSync(settings_path)) {
        var settings_data = fs.readFileSync(settings_path);
        settings = JSON.parse(settings_data);
    }
});

$(document).ready(function() {
    /**
     * Create JQuery DataTables for EDT HPC options file.
     * Update table rows, see tables_setter.js
     */
    history_table = $('#history-table').DataTable( {
        "scrollY": "132px",
        "scrollCollapse": true,
        "paging": false,
        "filter": false,
        "info": false,
        "ordering": false,
        "columnDefs": [
            { "width": "55px", "targets": [0, 1] },
            { "width": "15%", "targets": [2] },
            { "width": "320px", "targets": [3] }
          ]
    } );
    //add_hpc_files_rows();
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
                    { name: 'HPC Options', extensions: ['acf'] }
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
