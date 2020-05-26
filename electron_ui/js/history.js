var os_path = require('path');
var fs = require('fs');
const { remote } = require('electron');
const { dialog } = require('electron').remote;

settings_path = os_path.join(process.env.APPDATA, "build_downloader", "default_settings.json");
hpc_options_folder = os_path.join(process.env.APPDATA, "build_downloader", "HPC_Options");
history_file = os_path.join(process.env.APPDATA, "build_downloader", "installation_history.json");

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
        "data": get_history(),
        "columnDefs": [
            { "width": "55px", "targets": [0, 1] },
            { "width": "15%", "targets": [2] },
            { "width": "320px", "targets": [3] }
          ]
    } );
    //add_hpc_files_rows();
} );


function get_history(){
    /**
     * set history from JSON file.
     */
    if (fs.existsSync(history_file)) {
        let history = fs.readFileSync(history_file);
        history_json = JSON.parse(history);

        let history_data = [];
        for (var key in history_json){
            history_data.push(history_json[key]);
        }
        return history_data;
    }
}

$("#clear-button").click(function(){
    /**
     * If clean is requested delete the history file and refresh the page
     */
    answer = dialog.showMessageBoxSync(remote.getCurrentWindow(), {
            type: "question",
            buttons: ["Yes", "No"],
            message: "Do you want to clear history?"
        }
    )
    if (answer == 0) {
        fs.unlinkSync(history_file);
        location.reload();
        return false;
    };
});