let flags_data = [
    ['-additive', 'ANSYS Additive', '-additive'],
    ['-aqwa', 'ANSYS Aqwa', '-aqwa'],
    ['-autodyn', 'ANSYS Autodyn', '-autodyn'],
    ['-cfdpost', 'ANSYS CFD-Post', '-cfdpost'],
    ['-cfx', 'ANSYS CFX', '-cfx'],
    ['-chemkinpro', 'ANSYS Chemkin', '-chemkinpro'],
    ['-ansyscust', 'ANSYS Customization Files', '-ansyscust'],
    ['-discovery', 'ANSYS Discovery', '-discovery'],
    ['-spaceclaim', 'ANSYS Discovery SpaceClaim', '-spaceclaim'],
    ['-energico', 'ANSYS Energico', '-energico'],
    ['-ensight', 'ANSYS EnSight', '-ensight'],
    ['-fensapice', 'ANSYS FENSAP-ICE', '-fensapice'],
    ['-fluent', 'ANSYS Fluent', '-fluent'],
    ['-forte', 'ANSYS Forte', '-forte'],
    ['-icemcfd', 'ANSYS ICEM CFD', '-icemcfd'],
    ['-lsdyna', 'ANSYS LS-DYNA', '-lsdyna'],
    ['-mechapdl', 'ANSYS Mechanical APDL', '-mechapdl'],
    ['-mfl', 'ANSYS Model Fuel Library (Encrypted)', '-mfl'],
    ['-optislang', 'ANSYS optiSLang', '-optislang'],
    ['-polyflow', 'ANSYS Polyflow', '-polyflow'],
    ['-reactionwb', 'ANSYS Reaction Workbench', '-reactionwb'],
    ['-sherlock', 'ANSYS Sherlock', '-sherlock'],
    ['-speos', 'ANSYS SPEOS', '-speos'],
    ['-speoshpc', 'SPEOS HPC', '-speoshpc'],
    ['-turbogrid', 'ANSYS TurboGrid', '-turbogrid'],
    ['-acis', 'ACIS', '-acis'],
    ['-icepak', 'ANSYS Icepak', '-icepak'],
    ['-sc_config', 'ANSYS SpaceClaim Configuration*', '-sc_config'],
    ['-aview', 'ANSYS Viewer', '-aview'],
    ['-acad_plugin', 'AutoCAD Plugin', '-acad_plugin'],
    ['-acad_reader', 'AutoCAD Reader', '-acad_reader'],
    ['-adinventor_plugin', 'Autodesk Inventor Plugin', '-adinventor_plugin'],
    ['-adinventor_reader', 'Autodesk Inventor Reader', '-adinventor_reader'],
    ['-catia4', 'CATIA V4', '-catia4'],
    ['-catia5_plugin', 'CATIA 5 Plugin', '-catia5_plugin'],
    ['-catia5_reader', 'CATIA 5 Reader', '-catia5_reader'],
    ['-catia6', 'CATIA V6', '-catia6'],
    ['-cocreate', 'Creo Elements/Direct Modeling', '-cocreate'],
    ['-proe_plugin', 'Creo Parametric Plugin', '-proe_plugin'],
    ['-proe_reader', 'Creo Parametric Reader', '-proe_reader'],
    ['-jtopen', 'JTOpen', '-jtopen'],
    ['-dcs', 'Distributed Compute Services', '-dcs'],
    ['-ug_plugin', 'NX Plugin', '-ug_plugin'],
    ['-ug_reader', 'NX Reader', '-ug_reader'],
    ['-parasolid', 'Parasolid', '-parasolid'],
    ['-rsm', 'Remote Solve Manager Standalone Services', '-rsm'],
    ['-solidedge_plugin', 'Solid Edge Plugin', '-solidedge_plugin'],
    ['-solidedge_reader', 'Solid Edge Reader', '-solidedge_reader'],
    ['-solidworks_plugin', 'SOLIDWORKS Plugin', '-solidworks_plugin'],
    ['-solidworks_reader', 'SOLIDWORKS Reader', '-solidworks_reader'],
    ['-scdm_config', 'SpaceClaim Direct Modeler Configuration', '-scdm_config']
]



$(document).ready(function() {
    /**
     * Create JQuery DataTables for wb installation flags list
     * Remove sorting class for first column with checkboxes
     */
    flags_table = $('#wb-flags-table').DataTable( {
        "scrollY": "225px",
        "scrollCollapse": true,
        "paging": false,
        "filter": false,
        "info": false,
        'data': flags_data,
        'columnDefs': [{
           'targets': 0,
           'searchable':false,
           'orderable':false,
           'className': 'dt-body-center',
           'render': function (data, type, full, meta){
               return '<input type="checkbox" name="id[]" value="' 
                  + $('<div/>').text(data).html() + '">';
           }
        }]
    } );
    $(".check-column").removeClass("sorting_asc");
} );
