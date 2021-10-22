const {app, BrowserWindow, Menu, dialog} = require('electron');
const { autoUpdater } = require('electron-updater');
const ipc = require('electron').ipcMain;
const path = require('path');
const fs = require('fs');

autoUpdater.autoDownload = false;

setInterval(() => {
  autoUpdater.checkForUpdatesAndNotify()
}, 60000)

const version = app.getVersion();

app.allowRendererProcessReuse = false;    // use only false! otherwise tasks table render may fail
app.on('window-all-closed', () => {
    app.quit()
})

const about_options = {
        type: 'info',
        buttons: ['OK'],
        defaultId: 2,
        title: 'About',
        message: 'Ansys Pre-Release Installer v' + version,
        detail: 
            "Contact: betadownloader@ansys.com" +
            "\nCreated by: Maksim Beliaev" +
            "\nEmail: maksim.beliaev@ansys.com"             
    };



function show_agreement() {
    /**
     * Show always on top, so user cannot miss it
     */
    dialog.showMessageBox(new BrowserWindow({
        show: false,
        alwaysOnTop: true
      }),
      {
        type: 'info',
        buttons: ['OK'],
        defaultId: 2,
        title: 'Agreement',
        message: 'Ansys Beta Build Downloader Usage Agreement',
        detail: "This software collects information to support quality improvement, including user ID, version, " +
                "downloaded software, time and status of the installation."
    });
}

// Each object (dictionary) in a list is a dropdown item
let submenu_list = [
    {
        label:'Refresh Page',
        accelerator:process.platform == 'darwin' ? 'Command+R' : 'F5',
        click(){
            MainWindow.reload();
        }
    },
    {
        label:'About',
        click(){
            dialog.showMessageBox(null, about_options);
        }
    },
    {
        label:'Agreement',
        click(){
            show_agreement();
        }
    },
    {
        label:"What's New",
        click(){
            whats_new_window.show();
        }
    },
    {
        label: 'Quit',
        accelerator: "CmdOrCtrl+Q",
        click(){
            app.quit();
        }
    }
]

if (
    (app.isPackaged && !app.commandLine.hasSwitch("debug")) ||
    app.commandLine.hasSwitch("no-debug")
) {
    // for testing we may want to provide --no-debug flag to verify UI
    app_width = 1000;
} else {
    app_width = 2*1000;    // debug flag is sent or exe not built
    submenu_list.push({
        label:'Developer Tools',
        accelerator: 'Ctrl+Shift+I',
        role: "toggleDevTools"
    })
}

function create_settings_window() {
    let settings_window = new BrowserWindow({ 
        parent: MainWindow, 
        show: false, 
        modal: true,
        height: 600,
        width: 800,
        resizable: false,
        frame: false,
        webPreferences: {
            nodeIntegration: true,
            enableRemoteModule: true
        }
    });
    return settings_window;
}

app.on('ready', () => {
    MainWindow = new BrowserWindow({
        show: false,    // disable show from the beginning to avoid white screen, see ready-to-show
        webPreferences: {
            nodeIntegration: true,
            enableRemoteModule: true  // starting from V9
        },
        height: 650,
        width: app_width,
        resizable: false
	  });

    MainWindow.once('ready-to-show', () => {
        MainWindow.show()
    })

    // create new child to show What's New section in separate window
    whats_new_window = new BrowserWindow({ 
        parent: MainWindow, 
        show: false, 
        modal: true,
        height: 550,
        width: 650,
        resizable: false,
        frame: false,
        webPreferences: {
            nodeIntegration: true
        }
    });
    whats_new_window.loadURL('file://' + __dirname + '/web_pages/whatsnew.html');

    // load main page only after we show starting logo
    setTimeout(function(){
        MainWindow.loadURL('file://' + __dirname + '/web_pages/main.html');
    }, 1500);

    setTimeout(function(){
        autoUpdater.checkForUpdatesAndNotify();
    }, 7000);


    MainWindow.loadURL('file://' + __dirname + '/web_pages/starter.html');


    MainWindow.on('closed', () => {
        app.quit()
    })


    autoUpdater.on('update-available', () => {
        MainWindow.webContents.send('update_available');
    });
    autoUpdater.on('update-downloaded', () => {
        MainWindow.webContents.send('update_downloaded');
    });

    ipc.on('restart_app', () => {
          autoUpdater.quitAndInstall(isSilent=true, forceRunAfter=true);
    });

    ipc.on('download_update', () => {
          autoUpdater.downloadUpdate()
    });

    // event to open What's New window on signal from IPC
    ipc.on('whatsnew_show', () => {
        whats_new_window.show()
    });

    ipc.on('whatsnew_hide', (event, not_show_again, settings) => {
        if (not_show_again){
            app_folder = path.join(app.getPath("appData"), "build_downloader")
            whatisnew_path = path.join(app_folder, "whatisnew.json");
    
            let data = JSON.stringify(settings, null, 4);
            fs.writeFileSync(whatisnew_path, data);
        }
        whats_new_window.hide()
    });

    // signals for WB flags window
    ipc.on('wb_flags_show', () => {
        // create separate window for WB installation flags
        wb_flags_window = create_settings_window();
        wb_flags_window.loadURL('file://' + __dirname + '/web_pages/wb_flags.html');
        wb_flags_window.show()
    });

    ipc.on('wb_flags_hide', () => {
        wb_flags_window.close()
    });

    // signals for AEDT HPC/registry window
    ipc.on('aedt_registry_show', () => {
        aedt_registry_window = create_settings_window();
        aedt_registry_window.loadURL('file://' + __dirname + '/web_pages/aedt_registry.html');
        aedt_registry_window.show()
    });

    ipc.on('aedt_registry_hide', () => {
        aedt_registry_window.close()
    });

    ipc.on('agreement_show', () => {
        // signals to show usage agreement
        show_agreement();
    });

    var products_dict = {};
    ipc.on("get-products", () => {
        // event that requests to send products dictionary to browser window
        MainWindow.webContents.send("products", products_dict);
    });

    ipc.on("set-products", (event, products) => {
        // event that receives from browser window updated dict with products and stores in main process
        products_dict = products;
    });

    const mainMenuTemplate =    [
        {
            label: 'Menu',
            submenu: submenu_list
        }
    ];
        
    const mainMenu = Menu.buildFromTemplate(mainMenuTemplate);
    Menu.setApplicationMenu(mainMenu);
});


