function set_default_tooltips_main(){
    /**
     * Set tooltips on the main page
     */
    set_tooltip("password",  "Retrieval of Artifactory Encrypted Password Instructions:\n" +
    "1. Log into Artifactory\n" +
    "2. Click on your username (top right)\n" +
    "3. Enter your password to Unlock Artifactory Encrypted Password\n" +
    "4. Copy Artifactory Encrypted Password\n" +
    "[Note] Artifactory password is not valid for other artifactories.\n" +
     "Encrypted password will change anytime your SSO password changes.", true);

     set_tooltip("username",  "Ansys UserID");

     set_tooltip("schedule-table-div",  "Click on a row to unschedule specific task");

}

function set_default_tooltips_settings(){
    /**
     * Set tooltips on the settings page
     */
    set_tooltip("force_install_label",
        "Not recommended to check. If checked will force install build of the same  date.\n" +
        "For example you have installed build of 20th of May and try to download" +
        "and install next day, application will identify that new build was not added" +
        "to artifactory and will skip the installation", true);

    set_tooltip("wb_flags", "Product\tProduct Flag\nANSYS Additive\t-additive\nANSYS Aqwa\t-aqwa\nANSYS Autodyn\t-autodyn\nANSYS CFD-Post\t-cfdpost\nANSYS CFX\t-cfx\nANSYS Chemkin\t-chemkinpro\nANSYS Customization Files\t-ansyscust\nANSYS Discovery AIM\t-aim\nANSYS Discovery\t-live\nANSYS Discovery SpaceClaim\t-spaceclaim\nANSYS Energico\t-energico\nANSYS EnSight\t-ensight\nANSYS FENSAP-ICE\t-fensapice\nANSYS Fluent\t-fluent\nANSYS Forte\t-forte\nANSYS ICEM CFD\t-icemcfd\nANSYS LS-DYNA\t-lsdyna\nANSYS Mechanical APDL\t-mechapdl\nANSYS Model Fuel Library (Encrypted)\t-mfl\nANSYS optiSLang\t-optislang\nANSYS Polyflow\t-polyflow\nANSYS Reaction Workbench\t-reactionwb\nANSYS Sherlock\t-sherlock\nANSYS SPEOS\t-speos\nANSYS TurboGrid\t-turbogrid\nNote: Installing any of the above products will install ANSYS Workbench.\n\t \nACIS\t-acis\nANSYS Icepak\t-icepak\nANSYS SpaceClaim Configuration*\t-sc_config\nANSYS Viewer\t-aview\nAutoCAD Plugin\t-acad_plugin\nAutoCAD Reader\t-acad_reader\nAutodesk Inventor Plugin\t-adinventor_plugin\nAutodesk Inventor Reader\t-adinventor_reader\nCATIA V4\t-catia4\nCATIA 5 Plugin\t-catia5_plugin\nCATIA 5 Reader\t-catia5_reader\nCATIA V6\t-catia6\nCreo Elements/Direct Modeling\t-cocreate\nCreo Parametric Plugin\t-proe_plugin\nCreo Parametric Reader\t-proe_reader\nJTOpen\t-jtopen\nDistributed Compute Services\t-dcs\nNX Plugin\t-ug_plugin\nNX Reader\t-ug_reader\nParasolid\t-parasolid\nRemote Solve Manager Standalone Services\t-rsm\nSolid Edge Plugin\t-solidedge_plugin\nSolid Edge Reader\t-solidedge_reader\nSOLIDWORKS Plugin\t-solidworks_plugin\nSOLIDWORKS Reader\t-solidworks_reader\nSpaceClaim Direct Modeler Configuration*\t-scdm_config", true, "left")

    set_tooltip("install_path",
        "Root path would be appended by:\n\\AnsysEM\\AnsysEMXX.X for EDT\nor \n\\ANSYS Inc\\vXXX for WB");

    set_tooltip("hpc-options-table-div", "Click on a row to remove options file")
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
     * Show tooltip in specific title for 3.5s. After destroy and revert back default tooltips
     * @param  {} prop_title: tooltip message
     */
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