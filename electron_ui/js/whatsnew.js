const { ipcRenderer } = require('electron');


// see whatnew_list.js for the list of updates

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
        $('#whatsnew-div').append('<div class="whats-version">' + key + '</div>').append(
            '<div class="whats-text">' + whatsnew[key].split("\n").join("<br>") + '</div>'
        );
    });
    
}