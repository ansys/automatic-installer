const {app, BrowserWindow, Menu} = require('electron');
const {dialog} = require('electron');
const ipc = require('electron').ipcMain;


const version = "0.1";
const build_date = "02 May 2020";


app.on('window-all-closed', () => {
  app.quit()
})

const about_options = {
    type: 'info',
    buttons: ['OK'],
    defaultId: 2,
    title: 'About',
    message: 'Ansys Beta build Downloader v' + version,
    detail: 'Build date: ' + build_date + "\nCreated by: Maksim Beliaev\nEmail: maksim.beliaev@ansys.com",
  };


app.on('ready', () => {

	var MainWindow = new BrowserWindow({
	    show: false,  // disable show from the beginning to avoid white screen, see ready-to-show
        webPreferences: {
            nodeIntegration: true
        },
		height: 600,
		width: 2*1000,
		resizable: false
	});
	
    MainWindow.once('ready-to-show', () => {
        MainWindow.show()
    })

    // load main page only after we show starting logo
	setTimeout(function(){
        MainWindow.loadURL('file://' + __dirname + '/main.html');
    }, 3700);

    MainWindow.loadURL('file://' + __dirname + '/starter.html');


	MainWindow.on('closed', () => {
  		app.quit()
	})

	const mainMenuTemplate =  [
      // Each object (dictionary) is a dropdown
      {
        label: 'Menu',
        submenu:[
          {
            label:'About',
            click(){
              dialog.showMessageBox(null, about_options);
            }
          },
          {
            label:'Help',
            click(){
              MainWindow.webContents.send('item:clear');
            }
          },
          {
            label: 'Quit',
            accelerator:process.platform == 'darwin' ? 'Command+Q' : 'Ctrl+Q',
            click(){
              app.quit();
            }
          }
        ]
      }
    ];
    
    const mainMenu = Menu.buildFromTemplate(mainMenuTemplate);
    // Menu.setApplicationMenu(mainMenu);

});