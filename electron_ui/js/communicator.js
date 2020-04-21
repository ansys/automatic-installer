var path = require('path');
const ipc = require('electron').ipcRenderer;
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
          // received a message sent from the Python script (a simple "print" statement)
          if (message.includes("active_tasks")){
                tasks_list = JSON.parse((message.split(/ (.*)/)[1]).replace(/'/g, '"'));
                add_task_rows(tasks_list);
          }
          console.log(message);
          var nodeConsole = require('console');
          var myConsole = new nodeConsole.Console(process.stdout, process.stderr);
          myConsole.log('\x1b[36m%s\x1b[0m', 'PIPED FROM PYTHON PROGRAM: ' + message.toString());
        });

function add_task_rows(tasks_list) {
    var table = document.getElementById("schedule-table");

    for (var i in tasks_list) {
        var row = table.insertRow(1); // after header
        var cell_product = row.insertCell(0);
        cell_product.innerHTML = tasks_list[i].product;
        cell_product.classList.add("tg-baqh");
        cell_product.classList.add("product-column");

        var cell_version = row.insertCell(1);
        cell_version.innerHTML = tasks_list[i].version;
        cell_version.classList.add("tg-baqh");
        cell_version.classList.add("version-column");

        var cell_schedule = row.insertCell(2);
        cell_schedule.innerHTML = tasks_list[i].schedule_time;
        cell_schedule.classList.add("tg-baqh");
        cell_schedule.classList.add("schedule-column");
    }

    if (tasks_list.length < 3) {
        for (i = 0; i < 3 - tasks_list.length; i++) {
            var row = table.insertRow(-1); // at the end
            var cell_product = row.insertCell(0);
            cell_product.innerHTML = "";
            cell_product.classList.add("tg-baqh");
            cell_product.classList.add("product-column");

            var cell_version = row.insertCell(1);
            cell_version.innerHTML = "";
            cell_version.classList.add("tg-baqh");
            cell_version.classList.add("version-column");

            var cell_schedule = row.insertCell(2);
            cell_schedule.innerHTML = "";
            cell_schedule.classList.add("tg-baqh");
            cell_schedule.classList.add("schedule-column");
        }
    }
}
        
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
