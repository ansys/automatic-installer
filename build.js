const electronInstaller = require('electron-winstaller');


// In this case, we can use relative paths
var settings = {
    appDirectory: './electron_ui/electron_build/ansys_build_downloader-win32-x64',
    outputDirectory: './build_installers'
  };

resultPromise = electronInstaller.createWindowsInstaller(settings);
 
resultPromise.then(() => {
    console.log("The installers of your application were succesfully created !");
}, (e) => {
    console.log(`Well, sometimes you are not so lucky: ${e.message}`)
});