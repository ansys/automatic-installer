var path = require('path');
const {remote} = require('electron');
const {dialog} = require('electron').remote;
let {PythonShell} = require('python-shell');

//options to run when compiled to exe
//let options = {
//  mode: 'text',
//  pythonPath: "resources/app/python_build/electron_backend.exe"
//};
//
//pyshell = new PythonShell(' ', options);

pyshell = new PythonShell('electron_backend.py');
pyshell.on('message', function (message) {
          /** received a message sent from the Python script (a simple "print" statement)
           * Depending on the content of the message fire different functions
          */
          if (message.includes("active_tasks")){
                tasks_list = JSON.parse((message.split(/ (.*)/)[1]).replace(/'/g, '"'));
                add_task_rows(tasks_list);
          }
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
  }
}


document.addEventListener('DOMContentLoaded', function() {

  document.getElementById("install-once-button").addEventListener("click", launchPython);
  document.getElementById("schedule-button").addEventListener("click", launchPython);

})
