var os_path = require('path');
var fs = require('fs');
const {remote} = require('electron');
const { dialog } = require('electron').remote;

settings_path = os_path.join(process.env.APPDATA, "build_downloader", "default_settings.json");
hpc_options_folder = os_path.join(process.env.APPDATA, "build_downloader", "HPC_Options")

$("#install_path, #download_path").click(
    function(){
        dialog.showOpenDialog(remote.getCurrentWindow(), {
                defaultPath: this.value,
                properties: [ 'openDirectory' ]
            }).then(
            result => {
                if (result.canceled == false) {
                    this.value = result.filePaths;
                    save_settings.call(this);
                }
            }).catch(err => {
                  console.log(err)
                })
    }
);


window.onload = function() {
    if (fs.existsSync(settings_path)) {
        var settings_data = fs.readFileSync(settings_path);
        settings = JSON.parse(settings_data);

        $("#install_path").val(settings.install_path);
        $("#download_path").val(settings.download_path);
        $("#delete_zip").prop("checked", settings.delete_zip);
        $("#force_install").prop("checked", settings.force_install);
        $("#wb_flags").val(settings.wb_flags);
    }

    set_default_tooltips_settings();

    if (!fs.existsSync(hpc_options_folder)) fs.mkdirSync(hpc_options_folder);
    add_hpc_files_rows();
}

function add_hpc_files_rows() {
    var table_container = document.getElementById("hpc-options-table");
    var table = table_container.getElementsByTagName("tbody")[0];
    $('#hpc-options-table tbody').empty();

    var files_list = fs.readdirSync(hpc_options_folder);
    files_list = files_list.filter(name => name.includes(".acf"));
    files_list.sort(function (a, b) {
        if (a.slice(0, 3) > b.slice(0, 3)) {return -1;}
        else if (b.slice(0, 3) > a.slice(0, 3)) {return 1;}
        return 0;
    });

    for (var i in files_list) {

        var row = table.insertRow(0); // after header
        var cell_product = row.insertCell(0);
        cell_product.innerHTML = os_path.join(hpc_options_folder, files_list[i]);
        cell_product.classList.add("tg-gzer");
        cell_product.classList.add("file-column");

        var createClickHandler = function(selected_row) {
                return function() {
                                        var file_name = selected_row.getElementsByTagName("td")[0].innerHTML;
                                        answer = dialog.showMessageBoxSync(remote.getCurrentWindow(), {
                                                type: "question",
                                                buttons: ["Yes", "No"],
                                                message: "Do you want permanently delete " + file_name + "?"
                                            }
                                        )

                                        if (answer == 0) {
                                            fs.unlinkSync(file_name);
                                            add_hpc_files_rows();
                                        }
                                 };
        };

        row.onclick = createClickHandler(row);
    }

    if (files_list.length < 4) {
        for (i = 0; i < 4 - files_list.length; i++) {
            var row = table.insertRow(-1); // at the end
            var cell_product = row.insertCell(0);
            cell_product.innerHTML = "";
            cell_product.classList.add("tg-gzer");
            cell_product.classList.add("file-column");
        }
    }
}

$("#install_path, #download_path, #password, #force_install, #delete_zip, #wb_flags").bind("change", save_settings);

var save_settings = function(){
  if (this.id == "force_install" || this.id == "delete_zip"){
    settings[this.id] = this.checked;
  } else {
    settings[this.id] = this.value;
  }

  let data = JSON.stringify(settings, null, 4);
  fs.writeFileSync(settings_path, data);

};
