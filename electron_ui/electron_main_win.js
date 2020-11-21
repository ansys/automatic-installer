const {app, BrowserWindow, Menu, dialog} = require('electron');
const { autoUpdater } = require('electron-updater');
const ipc = require('electron').ipcMain;
const os_path = require('path');
const fs = require('fs');

const updateServer = 'http://ottbld02:1337';
let arch = 'win64';

const feed = `${updateServer}/update/${arch}`;
autoUpdater.setFeedURL(feed);
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
        message: 'Ansys Beta Build Downloader v' + version,
        detail: 
            "Contact: betadownloader@ansys.com" +
            "\nCreated by: Maksim Beliaev" +
            "\nEmail: maksim.beliaev@ansys.com"             
    };

const usage_agreement = {
        type: 'info',
        buttons: ['OK'],
        defaultId: 2,
        title: 'Agreement',
        message: 'Ansys Beta Build Downloader Usage Agreement',
        detail: "This software collects information to support quality improvement, including user ID, version, " +
                "downloaded software, time and status of the installation."
    };

global.agreement = usage_agreement;

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
            dialog.showMessageBox(null, usage_agreement);
        }
    },
    {
        label:"What's New",
        click(){
            child.show();
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

if (app.isPackaged) {
        var app_width = 1000;    // production
} else {
        var app_width = 2*1000;;    // develop
        submenu_list.push({
            label:'Developer Tools',
            accelerator:process.platform == 'darwin' ? 'Command+R' : 'Ctrl+Shift+I',
            role: "toggleDevTools"
        })
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
    child = new BrowserWindow({ 
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
    child.loadURL('file://' + __dirname + '/whatsnew.html');

    // load main page only after we show starting logo
	  setTimeout(function(){
        MainWindow.loadURL('file://' + __dirname + '/main.html');
        autoUpdater.checkForUpdatesAndNotify();
    }, 3700);

    MainWindow.loadURL('file://' + __dirname + '/starter.html');


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
          autoUpdater.quitAndInstall();
    });

    ipc.on('download_update', () => {
          autoUpdater.downloadUpdate()
    });

    // event to open What's New window on signal from IPC
    ipc.on('whatsnew_show', () => {
        child.show()
    });

    ipc.on('whatsnew_hide', (event, not_show_again, settings) => {
        if (not_show_again){
            app_folder = os_path.join(app.getPath("appData"), "build_downloader")
            whatisnew_path = os_path.join(app_folder, "whatisnew.json");
    
            let data = JSON.stringify(settings, null, 4);
            fs.writeFileSync(whatisnew_path, data);
        }
        child.hide()
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


