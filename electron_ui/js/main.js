var os_path = require('path');
var fs = require('fs');
var axios = require('axios');
const { shell } = require('electron');


artifactory_dict = {
    'Austin': 'http://ausatsrv01.ansys.com:8080/artifactory',
    'Boulder': 'http://bouatsrv01:8080/artifactory',
    'Canonsburg': 'http://canartifactory.ansys.com:8080/artifactory',
    'Concord': 'http://convmartifact.win.ansys.com:8080/artifactory',
    'Darmstadt': 'http://darvmartifact.win.ansys.com:8080/artifactory',
    'Evanston': 'http://evavmartifact:8080/artifactory',
    'Gothenburg': 'http://gotvmartifact1:8080/artifactory',
    'Hannover': 'http://hanartifact1.ansys.com:8080/artifactory',
    'Horsham': 'http://horvmartifact1.ansys.com:8080/artifactory',
    'Lebanon': 'http://lebartifactory.win.ansys.com:8080/artifactory',
    'Lyon': 'http://lyovmartifact.win.ansys.com:8080/artifactory',
    'MiltonPark': 'http://milvmartifact.win.ansys.com:8080/artifactory',
    'Otterfing': 'http://ottvmartifact.win.ansys.com:8080/artifactory',
    'Pune': 'http://punvmartifact.win.ansys.com:8080/artifactory',
    'Sheffield': 'http://shfvmartifact.win.ansys.com:8080/artifactory',
    'SanJose': 'http://sjoartsrv01.ansys.com:8080/artifactory',
    'Waterloo': 'http://watatsrv01.ansys.com:8080/artifactory'
};

app_folder = os_path.join(app.getPath("appData"), "build_downloader")
settings_path = os_path.join(app_folder, "default_settings.json");
all_days = ["mo", "tu", "we", "th", "fr", "sa", "su"]

window.onload = function() {
    /**
     * Function is fired on the load the window. Verifies that settings file exists in APPDATA.
     * If exists => read settings and populate UI data from the file
     * If not => create default file with settings and dump it to settings file. Then use these settings for UI.
     * 
     * Gets active schtasks.
     * Runs function to set tooltips text
     */

    if (!fs.existsSync(settings_path)) {
        settings = {
            "username": process.env.USERNAME,
            "install_path": get_previous_edt_path(),
            "artifactory": "Otterfing",
            "password": {"Otterfing": ""},
            "delete_zip": true,
            "download_path": app.getPath("temp"),
            "version": "",
            "wb_flags": "",
            "days": [
                "sa"
            ],
            "time": "01:30",
            "force_install": false
        }

        if (!fs.existsSync(app_folder)) fs.mkdirSync(app_folder);
        let data = JSON.stringify(settings, null, 4);
        fs.writeFileSync(settings_path, data);
    } else {
        var settings_data = fs.readFileSync(settings_path);
        settings = JSON.parse(settings_data);
    }

    $("#username").val(settings.username);
    change_password();


    for (var i in all_days) {
        $(`#${all_days[i]}-checkbox`).prop("checked", settings.days.includes(all_days[i]));
    }

    $("#time").val(settings.time);


    set_selector("artifactory", Object.keys(artifactory_dict), settings.artifactory);

    get_active_tasks();
    request_builds();
    set_default_tooltips_main();
}



function get_previous_edt_path() {
    /**
     * parse environment variables and search for EM installation. If some build was installed 
     * propose the same directory
     * Otherwise search for previous WB installation and propose it
     * If nothing is found propose C:/program files
    */ 
    all_vars = Object.keys(process.env);
    var env_var = ""
    for (var i in all_vars){
        if (all_vars[i].toLowerCase().includes("ansysem_root")) env_var = process.env[all_vars[i]];
    }

    if (!env_var){
        // search for WB env var match eg "ANSYS202_DIR"
        const regex_str = /ansys[0-9]{3,}_dir/;
        for (var i in all_vars){
            if (all_vars[i].toLowerCase().match(regex_str)) env_var = process.env[all_vars[i]];
        }
    }
    if (!env_var){
        return "C:\\Program Files";
    }
    return path.dirname(path.dirname(path.dirname(env_var)));
}


function set_selector(id, obj_list, default_item="") {
    /**
     * @param  {string} id: id of the drop down menu
     * @param  {Array} obj_list: list of objects to fill in the menu
     * @param  {string} default_item="": default selection
     */
    var selector = document.getElementById(id);
    $("#" + id).empty();

    for (var i in obj_list) {
        option = document.createElement("option");
        option.textContent = obj_list[i];
        option.value = obj_list[i];
        selector.add(option);
    }

    if(obj_list.includes(default_item)) {
        selector.value = default_item;
    }
}

var save_settings = function () {
    /**
     * Dump settings to the JSON file in APPDATA. Fired on any change in the UI
    */
    const all_checkboxes = ["mo-checkbox", "tu-checkbox", "we-checkbox", "th-checkbox", "fr-checkbox",
            "sa-checkbox", "su-checkbox"];

    if (all_checkboxes.includes(this.id)) {
        var new_days = [];
        for (var i in all_checkboxes) {
            checkbox = $("#" + all_checkboxes[i])[0];
            if (checkbox.checked == true) {
                new_days.push(all_checkboxes[i].slice(0, 2));
            }
        }
        settings.days = new_days;
    } else if (this.id === "password"){
        settings.password[settings.artifactory] = this.value;
    } else {
        settings[this.id] = this.value;
    }

    let data = JSON.stringify(settings, null, 4);
    fs.writeFileSync(settings_path, data);
}


var request_builds = function (){
    /**
     * Send request to the server using axios. Try to retrive info about 
     * available builds on artifactory
    */
   $("#version").empty();
   $("#version").append($('<option>', {value:1, text:"Loading data..."}))

    if (!settings.username) {
        error_tooltip.call($('#username'), "Provide your Ansys User ID");
        return;
    }

    if (!settings.password[settings.artifactory]) {
        error_tooltip.call($('#password'), "Provide Artifactory unique password");
        return;
    }

    axios.get(artifactory_dict[settings.artifactory] + '/api/repositories', {
      auth: {
        username: settings.username,
        password: settings.password[settings.artifactory]
      },
      timeout: 30000
    })
      .then((response) => {
         if (response.status == 200) {
            get_builds(response.data);
         }
      })
      .catch((err) => {
        if (!err.response && !err.code) {
            error_tooltip.call($('#artifactory'), "Check that you are on VPN and retry in 10s (F5)");
        } else if (err.code === 'ECONNABORTED'){
            error_tooltip.call($('#username'), "Timeout on connection, check Ansys User ID");
            error_tooltip.call($('#password'), "Timeout on connection, check Password or/and retry (F5)");
        } else if (err.response.status == 401){
            error_tooltip.call($('#username'), "Bad credentials, check Ansys User ID");
            error_tooltip.call($('#password'), "Bad credentials, check Artifactory unique password");
         }
      });
}


function get_builds(artifacts_list){
    /**
     * Parses information from the server. If see EBU or WB build extract version and add to the list
     */
    let version_list = [];
    for (var i  in artifacts_list) {
        repo = artifacts_list[i]["key"];
        if (repo.includes("EBU_Certified")){
            var version = repo.split("_")[0] + "_EDT"
            if (!version_list.includes(version)) {
                version_list.push(version);
            }
        } else if (repo.includes("Certified") &&
                   !repo.includes("Licensing") &&
                   !repo.includes("TEST")){
            var version = repo.split("_")[0] + "_WB";
            if (!version_list.includes(version)) {
                version_list.push(version);
            }
        }
    }
    version_list.sort(function (a, b) {
        if (a.slice(1, 6) > b.slice(1, 6)) {return -1;}
        else if (b.slice(1, 6) > a.slice(1, 6)) {return 1;}
        return 0;
    });

    if(version_list.includes(settings.version)){
        set_selector("version", version_list, settings.version);
    } else {
        version = document.getElementById("version");
        set_selector("version", version_list);
        save_settings.call($("#version")[0]);
    }
}


function open_artifactory_site(){
    url = artifactory_dict[$("#artifactory").val()]
    shell.openExternal(url);
}

const change_password = function (){
    /**
     * Password is stored in settings in another dictionary (Object), extract it for selected artifactory
     */
    password = (settings.password.hasOwnProperty(settings.artifactory)) ? settings.password[settings.artifactory] : "";
    $("#password").val(password);
}

$('.clockpicker').clockpicker({
    /**
     * enable JQuery clockpicker for time selection for scheduling
     */
    autoclose: true,
    placement: 'left'
});

$("#artifactory, #username, #password, #time, #version, .days-checkbox").bind("change", save_settings);
$("#artifactory").bind("change", change_password);
$("#artifactory").bind("dblclick", open_artifactory_site);
$("#artifactory, #username, #password").bind("change", request_builds);

$("#schedule-button").click(function (){
    /**
     * Execute when click on schedule button. Verify that at least one day is selected
     * If version is empty or not equal to drop menu => server is not grabbed yet => return
     * 
     * Make copy of settings file to another file for scheduling
     * If all checks are fine then set a task and retrieve a new tasks list
     */
    if(settings.days.length == 0){
        alert("At least one day should be selected!");
        return;
    }

    if(settings.version == $("#version")[0].value && settings.version){
        var scheduled_settings = os_path.join(app_folder, "settings_" + settings.version + ".json");
        fs.copyFileSync(settings_path, scheduled_settings, (err) => {
            if (err) throw err;
        });
        schedule_task(scheduled_settings);

        setTimeout(() => {
            get_active_tasks();
        }, 1000);
        
    } else {
        alert("Version does not exist on artifactory");
    }
})

$("#install-once-button").click(function (){
    /**
     * Execute when click on install once button.
     * If version is empty or not equal to drop menu => server is not grabbed yet => return
     * 
     * Make copy of settings file to another file for installing once
     */
    if(settings.version == $("#version")[0].value && settings.version){
        var install_once_settings = os_path.join(app_folder, "install_once_settings_" + settings.version + ".json");
        fs.copyFileSync(settings_path, install_once_settings, (err) => {
            if (err) throw err;
        });
        install_once(install_once_settings); 
        alert("Installation started! You can check the progress on Installation History page")     
    } else {
        alert("Version does not exist on artifactory");
    }
})