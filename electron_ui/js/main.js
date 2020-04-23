var os_path = require('path');
var fs = require('fs');
var axios = require('axios');

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

app_folder = os_path.join(process.env.APPDATA, "build_downloader")
settings_path = os_path.join(app_folder, "default_settings.json");
all_days = ["mo", "tu", "we", "th", "fr", "sa", "su"]

window.onload = function() {

    if (!fs.existsSync(settings_path)) {
        settings = {
            "username": process.env.USERNAME,
            "install_path": get_previous_edt_path(),
            "artifactory": "Otterfing",
            "password": "",
            "delete_zip": true,
            "download_path": process.env.TEMP,
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
    $("#password").val(settings.password);


    for (var i in all_days) {
        $(`#${all_days[i]}-checkbox`).prop("checked", settings.days.includes(all_days[i]));
    }

    $("#time").val(settings.time);


    set_selector("artifactory", Object.keys(artifactory_dict), settings.artifactory);

    pyshell.send('get_active_tasks');
    request_builds();
}

window.onbeforeunload = function(){
    pyshell.send('exit');
    pyshell.end(function (err,code,signal) {
        if (err) throw err;
        console.log('The exit code was: ' + code);
        console.log('The exit signal was: ' + signal);
        console.log('finished');
    });
}

function get_previous_edt_path() {
    all_vars = Object.keys(process.env);
    var env_var = ""
    for (var i in all_vars){
        if (all_vars[i].includes("ANSYSEM")) env_var = process.env[all_vars[i]];
    }

    if (!env_var){
        return "C:\\Program Files";
    } else {
        return path.dirname(path.dirname(path.dirname(env_var)));
    }
}

function set_selector(id, obj_list, default_item="") {
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
      } else {
        settings[this.id] = this.value;
      }

      let data = JSON.stringify(settings, null, 4);
      fs.writeFileSync(settings_path, data);
}

var timepicker = new TimePicker('time', {
  lang: 'en',
  theme: 'dark'
});

timepicker.on('change', function(evt) {
  var value = (evt.hour || '00') + ':' + (evt.minute || '00');
  evt.element.value = value;
  save_settings.call(evt.element);
});

var request_builds = function (){
    if (!settings.username) {
        error_tooltip.call($('#username'), "Provide your Ansys User ID");
        return;
    }

    if (!settings.password) {
        error_tooltip.call($('#password'), "Provide Artifactory unique password");
        return;
    }

    axios.get(artifactory_dict[settings.artifactory] + '/api/repositories', {
      auth: {
        username: settings.username,
        password: settings.password
      },
      timeout: 5000
    })
      .then((response) => {
        console.log(response.status);
         if (response.status == 200) {
            get_builds(response.data);
         }
      })
      .catch((err) => {
        if (!err.response) {
            error_tooltip.call($('#artifactory'), "Check that you are on VPN");
        } else if (err.code === 'ECONNABORTED'){
            error_tooltip.call($('#username'), "Timeout on connection, check Ansys User ID");
            error_tooltip.call($('#password'), "Timeout on connection, check Artifactory unique password");
        } else if (err.response.status == 401){
            error_tooltip.call($('#username'), "Bad credentials, check Ansys User ID");
            error_tooltip.call($('#password'), "Bad credentials, check Artifactory unique password");
         }
      });
}


var error_tooltip = function(prop_title) {
    this.tooltip('destroy');
    setTimeout(() => {this.tooltip({
                                title: prop_title,
                                placement: 'bottom'
                             }).tooltip('show');

    }, 150);
    this.attr('style', "border:#FF0000 2px solid;");

    setTimeout(() => {
        this.tooltip('destroy');
        this.attr('style', "border:#cccccc 1px solid;");

    }, 3500);
}

function get_builds(artifacts_list){

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
    set_selector("version", version_list);
}

$("#artifactory, #username, #password, .days-checkbox").bind("change", save_settings);
$("#artifactory").bind("change", request_builds);