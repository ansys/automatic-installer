const {app, BrowserWindow, Menu} = require('electron');
const { dialog } = require('electron');
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

	var ui = new BrowserWindow({
        webPreferences: {
            nodeIntegration: true
        },
		height: 600,
		width: 2*1000,
		resizable: false
	});
	ui.loadURL('file://' + __dirname + '/main.html');

	ui.on('closed', () => {
  		app.quit()
	})

	const mainMenuTemplate =  [
      // Each object is a dropdown
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
              mainWindow.webContents.send('item:clear');
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
    
    ipc.on('openJsonFile', () => { 
		
		var fs = require('fs');
		var fileName = './config.json';
		var file = require(fileName);

		// Asynchronous read
		// fs.readFile('config.json', function (err, data) {
		//   if (err) {
		//     return console.error(err);
		//   }
		//   console.log("Asynchronous read: " + data.toString());
		// });

		// Synchronous read
		var data = fs.readFileSync(fileName);
		var json = JSON.parse(data);

		var nodeConsole = require('console');
	    var myConsole = new nodeConsole.Console(process.stdout, process.stderr);
	    myConsole.log('\x1b[33m%s\x1b[0m','NOW IM IN main.js, AND GOT CALLED THROUGH ipc.send.');
	    myConsole.log('\x1b[33m%s\x1b[0m','DATA FROM config.json:');
		console.log('\x1b[33m%s\x1b[0m','A_MODE = ' + json.A_MODE);
		console.log('\x1b[33m%s\x1b[0m','B_MODE = ' + json.B_MODE);
		console.log('\x1b[33m%s\x1b[0m','C_MODE = ' + json.C_MODE);
		console.log('\x1b[33m%s\x1b[0m','D_MODE = ' + json.D_MODE);
		console.log('');
		
	});

});