var os_path = require('path');
var fs = require('fs');
const { remote } = require('electron');
const { app, dialog } = remote;
const ps = require('ps-node');

history_file = os_path.join(app.getPath("appData"), "build_downloader", "installation_history.json");
history_json = {}; 

$(document).ready(function() {
    /**
     * Create JQuery DataTables for EDT HPC options file.
     * Update table rows, see tables_setter.js
     */
    history_table = $('#history-table').DataTable( {
        "scrollY": "328px",
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
            { "visible": false, "targets": [5, 6]} // columns with PID and hash
        ]
    } );

    window.setInterval(update_history(), 7500);
    set_default_tooltips_history();
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
            history_data.push(history_json[key].concat(key));
        }
        return history_data;
    }
}

function update_history(){
    history_table.clear();
    let new_data = get_history();
    if (new_data) {
        history_table.rows.add(new_data);
        history_table.draw();
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

$('#history-table').on('click', 'tbody tr', function () {
    var row = history_table.row($(this)).data();
    if (row[0] == "In-Progress"){
        answer = dialog.showMessageBoxSync(remote.getCurrentWindow(), {
                type: "question",
                buttons: ["Yes", "No"],
                message: "Do you want to cancel installation of " + row[1] +"?"
            }
        )
        if (answer == 0) {
            ps.kill(row[5], function( err ) {
                if (err) {
                    throw new Error( err );
                }
                else {
                    console.log('Process has been killed!');
                }
            });

            var today = new Date();
            var date = today.getDate() + '-' + (today.getMonth()+1) + '-' + today.getFullYear();
            var time = today.getHours() + ":" + today.getMinutes();
            var date_time = date + ' ' + time;
            history_json[row[6]] = ["Failed", row[1], date_time, row[3], "User Aborted", row[5]];

            let data = JSON.stringify(history_json, null, 4);
            fs.writeFileSync(history_file, data);
            update_history();
        };
    }
});