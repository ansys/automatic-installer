var os_path = require('path');
var fs = require('fs');
const {remote} = require('electron');
const { dialog } = require('electron').remote;

settings_path = os_path.join(process.env.APPDATA, "build_downloader", "default_settings.json");

$("#install-path, #download-path").click(
    function(){
        dialog.showOpenDialog(remote.getCurrentWindow(), {properties: [ 'openDirectory' ] }).then(
            result => {
                if (result.canceled == false) {
                    $(`#${this.id}`).val(result.filePaths);
                }
            }).catch(err => {
                  console.log(err)
                })
    }
);


window.onload = function() {
    if (fs.existsSync(settings_path)) {
        var settings_data = fs.readFileSync(settings_path);
        settings_dict = JSON.parse(settings_data);

        $("#install-path").val(settings_dict.install_path);
        $("#download-path").val(settings_dict.download_path);
        $("#delete-zip").prop("checked", settings_dict.delete_zip);
        $("#wb-flags").val(settings_dict.wb_flags);
    }
}
