var path = require('path');
const ipc = require('electron').ipcRenderer;
let {PythonShell} = require('python-shell');

//options to run when compiled to exe
//let options = {
//  mode: 'text',
//  pythonPath: "dist/pythonExample/pythonExample.exe"
//};
//
//pyshell = new PythonShell(' ', options);

pyshell = new PythonShell('pythonExample.py');
pyshell.on('message', function (message) {
          // received a message sent from the Python script (a simple "print" statement)
          console.log(message);
          var nodeConsole = require('console');
          var myConsole = new nodeConsole.Console(process.stdout, process.stderr);
          myConsole.log('\x1b[36m%s\x1b[0m', 'PIPED FROM PYTHON PROGRAM: ' + message.toString());
        });
        
function launchPython(evt) {
  if (evt.srcElement.id == "install-once-button") {
      pyshell.send('install_once');
  }else if(evt.srcElement.id == "schedule-button"){
    pyshell.send('schedule_update');
  }else{
    pyshell.send('exit');
    pyshell.end(function (err,code,signal) {
      if (err) throw err;
      console.log('The exit code was: ' + code);
      console.log('The exit signal was: ' + signal);
      console.log('finished');
});

    
  }

}


document.addEventListener('DOMContentLoaded', function() {

  document.getElementById("install-once-button").addEventListener("click", launchPython);
  document.getElementById("schedule-button").addEventListener("click", launchPython);
  // document.getElementById("exit").addEventListener("click", launchPython);

  // document.getElementById("json").addEventListener("click", jsonForSettingsUse);

})
