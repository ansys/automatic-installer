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
    var table_container = document.getElementById("schedule-table");
    var table = table_container.getElementsByTagName("tbody")[0];
    $('#schedule-table tbody').empty();

    for (var i in tasks_list) {
        var row = table.insertRow(0); // after header
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

        var createClickHandler = function(selected_row) {
                return function() {
                                        product = selected_row.getElementsByTagName("td")[0].innerHTML;
                                        version = selected_row.getElementsByTagName("td")[1].innerHTML;
                                        answer = dialog.showMessageBoxSync(remote.getCurrentWindow(), {
                                                type: "question",
                                                buttons: ["Yes", "No"],
                                                message: "Do you want to delete scheduled task " + product +
                                                           " "+ version + "?"
                                            }
                                        )

                                        if (answer == 0) {
                                            pyshell.send('delete_task ' + product  + "_" + version);
                                            pyshell.send('get_active_tasks');
                                        }

                                 };
        };

        row.onclick = createClickHandler(row);
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

})
