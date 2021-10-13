var os_path = require('path');
var fs = require('fs');
var { remote, ipcRenderer } = require('electron');
var { app, dialog } = remote;

settings_path = os_path.join(app.getPath("appData"), "build_downloader", "default_settings.json");


$("#install_path, #download_path").click(
    /**
     * when click in the input box for download and installation path => open Electron dialog to select directory.
     * In HTML cursor is blurred to disable direct change in input field: see settings.html
     */
    function(){
        dialog.showOpenDialog(remote.getCurrentWindow(), {
                defaultPath: this.value,
                properties: [ 'openDirectory' ]
            }).then(
            result => {
                if (result.canceled == false) {
                    let selected_path = result.filePaths[0];
                    if (this.id == "install_path"){
                        if (selected_path.toLowerCase().endsWith("ansysem")){
                            selected_path = truncate_path("AnsysEM", selected_path);
                        } else if (selected_path.toLowerCase().endsWith("ansys inc")){
                            selected_path = truncate_path("Ansys Inc", selected_path);
                        }
                    }

                    this.value = selected_path;
                    save_settings.call(this);
                }
            }).catch(err => {
                  console.log(err)
                })
    }
);

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

$("#license_file").click(
    /**
     * When click on the button to add license file
     */
    function(){
        dialog.showOpenDialog(remote.getCurrentWindow(), {
                properties: ['openFile'],
                filters: [
                    { name: 'License files', extensions: ['lic'] },
                    { name: 'Text files', extensions: ['txt'] }
                ]
            }).then(
            result => {
                if (result.canceled == false) {
                    var lic_file = result.filePaths[0];
                    this.value = lic_file;
                    save_settings.call(this);
                }
            }).catch(err => {
                  console.log(err)
                })
    }
);


$("#wb_assoc").click(
    /**
     * When click on the button to add license file
     */
     function(){
        dialog.showOpenDialog(remote.getCurrentWindow(), {
                defaultPath: this.value,
                properties: [ 'openDirectory' ]
            }).then(
            result => {
                if (result.canceled == false) {
                    let selected_path = result.filePaths[0];
                    let assoc_exe = os_path.join(selected_path, "commonfiles", "tools", "winx64", "fileassoc.exe");
                    if (!fs.existsSync(assoc_exe)) {
                        dialog.showMessageBoxSync(remote.getCurrentWindow(), {
                                    type: "warning",
                                    title: "Warning!",
                                    buttons: ["OK"],
                                    message: "Association handler does not exist under: " + assoc_exe
                                }
                        )
                        return;
                    }
                    
                    this.value = selected_path;
                    save_settings.call(this);
                }
            }).catch(err => {
                  console.log(err)
                })
    }
);


$(document).ready(function() {
    /**
     * On load of the page set settings from JSON file.
     * Enable tooltips
     * If not directory with HPC options => create one
     */
    if (fs.existsSync(settings_path)) {
        var settings_data = fs.readFileSync(settings_path);
        settings = JSON.parse(settings_data);

        if (!("replace_shortcut" in settings)){
            settings.replace_shortcut = true;  // for backwards compatibility
        }

        if (!("license_file" in settings)){
            settings.license_file = "";  // for backwards compatibility
        }

        if (!("wb_assoc" in settings)){
            settings.wb_assoc = "";  // for backwards compatibility
        }

        $("#install_path").val(settings.install_path);
        $("#download_path").val(settings.download_path);
        $("#license_file").val(settings.license_file);
        $("#wb_assoc").val(settings.wb_assoc);
        $("#delete_zip").prop("checked", settings.delete_zip);
        $("#force_install").prop("checked", settings.force_install);
        $("#replace_shortcut").prop("checked", settings.replace_shortcut);
    }

    set_default_tooltips_settings();
});


var save_settings = function(){
    /** 
     * Save settings to the file on every UI change
    */
    if (this.id == "force_install" || this.id == "delete_zip" || this.id == "replace_shortcut"){
        settings[this.id] = this.checked;
    } else {
        settings[this.id] = this.value;
    }

    let data = JSON.stringify(settings, null, 4);
    fs.writeFileSync(settings_path, data);
};


$('#wb-flags-button').on('click', function(){
    /**
     * open new window with WB flags options
     */
     ipcRenderer.send('wb_flags_show');
});

$('#aedt-registry-button').on('click', function(){
    /**
     * open new window with HPC/registry options
     */
     ipcRenderer.send('aedt_registry_show');
});


$(
    "#install_path, #download_path, #license_file, #wb_assoc, #force_install, #delete_zip, #replace_shortcut"
    ).bind("change", save_settings);
