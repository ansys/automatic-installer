function set_default_tooltips_main(){
    /**
     * Set tooltips on the main page
     */
    set_tooltip("password",  "Retrieval of Artifactory Encrypted Password Instructions:\n" +
        "1. Double click on artifactory drop down menu\n" +
        "2. Log into Artifactory using SSO credentials\n" +
        "\t2.1 Click on your userID (top right)\n" +
        "\t2.2 Enter your password to Unlock Artifactory Encrypted Password\n" +
        "\t2.3 Copy over Artifactory Encrypted Password\n" +
        "[Note] Artifactory Encrypted Password is not valid for other artifactories.\n" +
        "Encrypted password will change anytime your SSO password changes.", true);

    set_tooltip("username",  "Ansys UserID");
    set_tooltip("artifactory",  "Select an artifactory and double click to open in Browser");

    set_tooltip("version",  "Latest available certified build would be downloaded");

    
    set_tooltip("time",  "Local computer time at which update will start.\n" + 
                    "Please try to use night time to decrease load on server");
    set_tooltip("schedule-table-div",  "Click on a row to unschedule specific task");

}

function set_default_tooltips_settings(){
    /**
     * Set tooltips on the settings page
     */
    set_tooltip("force_install_label",
        "Not recommended to check! By default if latest available build on artifactory is identical to one, " + 
        "already installed on this machine then installation will not proceed. This flag will skip the validation", 
        true);

    set_tooltip("wb-flags-table-div", "Select product flags. Note: Will install all if none selected");

    set_tooltip("install_path",
        "Root path would be appended by:\n\\AnsysEM\\AnsysEMXX.X for EDT\nor \n\\ANSYS Inc\\vXXX for WB");

    set_tooltip("hpc-options-table-div", "Click on a row to remove options file")
}

function set_default_tooltips_history(){
    set_tooltip("history-table-div", "Click on the 'In-Progress' row to cancel the installation")
}


function set_tooltip(id, text, align_left=false, place="bottom") {
    /**
     * Set tooltip for the HTML object
     * @param  {} id: id of the object
     * @param  {} text: tooltip text
     * @param  {} align_left=false: need to align text on the left?
     * @param  {} place="bottom": position of the tooltip
     */
    $("#" + id).tooltip({
                            title: text,
                            placement: place

                         })
                        .data('bs.tooltip')
                        .tip()
                        .addClass('default-tooltip')
                        //$("#" + id).tooltip("show");  // for debug

    if (align_left) {
        $("#" + id).data('bs.tooltip')
                    .tip()
                    .addClass("align-tooltip-left");
    }
}


var error_tooltip = function(prop_title) {
    /**
     * Set error tooltip (in red color). 
     * Show tooltip in specific title for 3.5s. After destroy and revert back default tooltips.
     * Since it is an error we cannot populate DropDown. We clear it and write this error message.
     * @param  {} prop_title: tooltip message
     */
    $("#version").empty();
    $("#version").append($('<option>', {value:1, text:prop_title}));

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
        setTimeout(() => {
            set_default_tooltips_main();
        }, 250);
    }, 3500);
}