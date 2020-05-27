var path = require('path');
const {app, dialog} = require('electron').remote;
let {PythonShell} = require('python-shell');
const execSync = require('child_process').execSync;
var parser = require('fast-xml-parser');


function get_task_details(task) {
      let task_data_dict = {
            "days": [],
            "time": "00:00",
            "product": "EDT",
            "version": "v201"
      }

      clean_task = task.replace(/(\r\n|\n|\r)/gm,""); //make it single line
      clean_task = clean_task.replace(/(^\s*<!--.*?-->)/g,""); //Remove comments

      if( parser.validate(clean_task) === true) {
            var jsonObj = parser.parse(clean_task, { ignoreNameSpace : false });
            console.log(jsonObj);
      } else {
            console.log("failed validation");
      }
}

let all_tasks = execSync('schtasks /query /xml').toString();
all_tasks = all_tasks.split("\r\n\r\n\r\n");
let ansys_tasks = [];

for(var i = 0; i < all_tasks.length; i++){
      if (all_tasks[i].includes("AnsysDownloader")){
            task_data_dict = get_task_details(all_tasks[i]);
            task_data_dict["schedule_time"] = (task_data_dict["days"]).join(", ") + " at " + task_data_dict["time"];
            ansys_tasks.push(task_data_dict);
      }
}
console.log(ansys_tasks);

