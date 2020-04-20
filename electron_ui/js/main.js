var os_path = require('path');
var fs = require('fs');

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

settings_path = os_path.join(process.env.APPDATA, "build_downloader", "default_settings.json");
all_days = ["mo", "tu", "we", "th", "fr", "sa", "su"]

window.onload = function() {

    var default_artfactory = "Otterfing";

    if (fs.existsSync(settings_path)) {
        var settings_data = fs.readFileSync(settings_path);
        settings = JSON.parse(settings_data);

        default_artfactory = settings.artifactory;
        $("#username").val(settings.username);
        $("#password").val(settings.password);


        for (var i in all_days) {
            $(`#${all_days[i]}-checkbox`).prop("checked", settings.days.includes(all_days[i]));
        }

        $("#time").val(settings.time);
    }

    set_selector("artifactory", artifactory_dict, default_artfactory);
}

function set_selector(id, dict, default_item="") {
    var selector = document.getElementById(id);

    for (var key in dict) {
        if(artifactory_dict.hasOwnProperty(key)) {
            option = document.createElement("option");
            option.textContent = key;
            option.value = key;
            selector.add(option);
        }
    }

    if(dict.hasOwnProperty(default_item)) {
        selector.value = default_item;
    }
}

var save_settings = function() {
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

$("#artifactory, #username, #password, .days-checkbox").bind("change", save_settings);
