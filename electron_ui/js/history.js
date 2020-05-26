var os_path = require('path');
var fs = require('fs');
const { remote } = require('electron');
const { dialog } = require('electron').remote;

history_file = os_path.join(process.env.APPDATA, "build_downloader", "installation_history.json");


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
            { "render": getImg, "targets": [0] },
            { "width": "55px", "targets": [0, 1] },
            { "width": "15%", "targets": [2] },
            { "width": "320px", "targets": [3] },
            { "className": "text-center", "targets": [0, 1, 2, 4] },
          ]
    } );
} );

function getImg(data, type, full, meta) {

    if (data === 'Failed') {
        return '<img class="img-in-table" src="images/failed.png" title="Failed" />';
    } else if (data === 'Success') {
        return '<img class="img-in-table" src="images/success.png" title="Success" />';
    } else {
        return '<img class="img-in-table" src="images/pending.png" title="In-Progress" />';
    }
}

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