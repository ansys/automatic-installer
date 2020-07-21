const {app, BrowserWindow, Menu, dialog} = require('electron');
const { autoUpdater } = require('electron-updater');
const ipc = require('electron').ipcMain;

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
        detail: "Created by: Maksim Beliaev" +
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
                            nodeIntegration: true
                    },
        height: 600,
        width: app_width,
        resizable: false
	  });

    MainWindow.once('ready-to-show', () => {
        MainWindow.show()
    })

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


    const mainMenuTemplate =    [
        {
            label: 'Menu',
            submenu: submenu_list
        }
    ];
        
    const mainMenu = Menu.buildFromTemplate(mainMenuTemplate);
    Menu.setApplicationMenu(mainMenu);
});


