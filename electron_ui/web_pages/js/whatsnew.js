var { ipcRenderer } = require('electron');
var fs = require('fs');
var path = require("path");

var whatsnew_data = fs.readFileSync(path.resolve(__dirname, "js", "whats_new.json"));
whatsnew = JSON.parse(whatsnew_data);

$("#whatsnew-ok-button").click(function (){
    let settings = {};
    if ($("#do_not_show_checkbox").prop("checked") == true) {
        settings = {"shown": Object.keys(whatsnew)}
    }
    let not_show_again = $("#do_not_show_checkbox").prop("checked");
    ipcRenderer.send('whatsnew_hide', not_show_again, settings);
})


window.onload = function() {
    /**
     * On window load generate list of new features from the dictionary
    */
    Object.keys(whatsnew).forEach(function(key) {
        if (Array.isArray(whatsnew[key])) {
            var val = whatsnew[key].join("");
        } else {
            var val = whatsnew[key]
        }
        $('#whatsnew-div').append('<div class="whats-version">' + 'v' + key + '</div>').append(
            '<div class="whats-text">' + val + '</div>'
        );
    });
    
}