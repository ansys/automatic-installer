
function add_task_rows(tasks_list) {
    var table_container = document.getElementById("schedule-table");
    var table = table_container.getElementsByTagName("tbody")[0];
    $('#schedule-table tbody').empty();

    for (var i in tasks_list) {
        var row = table.insertRow(0); // after header
        set_table_row(row, ["product-column", "version-column", "schedule-column"],
                        [tasks_list[i].product, tasks_list[i].version, tasks_list[i].schedule_time])

        var createClickHandler = function(selected_row) {
                return function() {
                                        product = selected_row.getElementsByTagName("td")[0].innerHTML;
                                        version = selected_row.getElementsByTagName("td")[1].innerHTML;
                                        answer = dialog.showMessageBoxSync(remote.getCurrentWindow(), {
                                                type: "question",
                                                buttons: ["Yes", "No"],
                                                message: "Do you want to delete scheduled task " + product +
                                                           " "+ version + "?"
                                            }
                                        )

                                        if (answer == 0) {
                                            pyshell.send('delete_task ' + product  + "_" + version);
                                            pyshell.send('get_active_tasks');
                                        }

                                 };
        };

        row.onclick = createClickHandler(row);
    }

    if (tasks_list.length < 3) {
        for (i = 0; i < 3 - tasks_list.length; i++) {
            var row = table.insertRow(-1); // at the end
            set_table_row(row, ["product-column", "version-column", "schedule-column"], ["", "", ""]);
        }
    }
}


function add_hpc_files_rows() {
    hpc_table.clear();

    var files_list = fs.readdirSync(hpc_options_folder);
    files_list = files_list.filter(name => name.includes(".acf"));

    for (var i in files_list) {
        var file_shorten_path = os_path.join("%APPDATA%", "build_downloader", "HPC_Options", files_list[i]);

        var row = hpc_table.row.add([file_shorten_path]).draw(false).node();
        var createClickHandler = function(selected_row) {
                return function() {
                                        var file_name = selected_row[0].innerText;
                                        answer = dialog.showMessageBoxSync(remote.getCurrentWindow(), {
                                                type: "question",
                                                buttons: ["Yes", "No"],
                                                message: "Do you want permanently delete " + file_name + "?"
                                            }
                                        )

                                        if (answer == 0) {
                                            fs.unlinkSync(file_name.replace('%APPDATA%', process.env.APPDATA));
                                            add_hpc_files_rows();
                                        }
                                 };
        };
        $(row).on("click", createClickHandler($(row)));
    }

    if (files_list.length < 4) {
        for (i = 0; i < 4 - files_list.length; i++) {
            var row = hpc_table.row.add([""]).draw(false).node();
        }
    }
}


function set_table_row(row, class_list, inner_html_list, main_class="tg-baqh"){
    for (var i in class_list) {
        var cell = row.insertCell(i);
        cell.innerHTML = inner_html_list[i];
        cell.classList.add(main_class);
        cell.classList.add(class_list[i]);
    }
}