import json
import os
import subprocess
import sys
import re
import xml.etree.ElementTree as ET

backend_exe = os.path.join(os.getcwd(), "python_build", "downloader_backend.exe")  # develop
#  backend_exe = os.path.join(os.getcwd(), "downloader_backend.exe")  # production


def get_task_details(task_name):
    """
    Function that extracts parameters of individual task
    :param task_name: XML string contained all data about the task
    :return task_data_dict = {"days": [],
                              "time": "00:00",
                              "product": "EDT",
                              "version": "v201"}
    """

    task_data_dict = {"days": [],
                      "time": "00:00",
                      "product": "EDT",
                      "version": "v201"}

    task_name = "\n".join(task_name.replace("\r\n", "").split("\r")[1:])  # remove empty lines

    schtasks = ET.fromstring(task_name)
    ns = {"win": re.search("{(.*)}Task", schtasks.tag).group(1)}  # name space

    calendar_trig = schtasks.find("win:Triggers/win:CalendarTrigger", ns)
    start_boundary = calendar_trig.find("win:StartBoundary", ns).text
    days = calendar_trig.find("win:ScheduleByWeek/win:DaysOfWeek", ns)
    for day in days:
        day_name = day.tag.split("}")[1][:2]
        task_data_dict["days"].append(day_name)

    task_data_dict["time"] = start_boundary.split("T")[1][:-3]

    uri = schtasks.find("win:RegistrationInfo/win:URI", ns)
    name = uri.text.split("\\")[2]
    task_data_dict["version"], task_data_dict["product"] = name.split("_")
    return task_data_dict


def get_active_schtasks():
    """
    Function to get schtasks that are already scheduled for EDT and WB
    UI is updated with this info
    """

    command = r"schtasks /query /xml"
    all_tasks = subprocess.check_output(command, shell=True).decode("ascii", errors="ignore")
    all_tasks = all_tasks.split("\r\n\r\n\r\n")

    ansys_tasks = []
    for task_name in all_tasks:
        if "AnsysDownloader" in task_name:
            task_data_dict = get_task_details(task_name)
            task_data_dict["schedule_time"] = ", ".join(task_data_dict["days"]) + " at " + task_data_dict["time"]
            ansys_tasks.append(task_data_dict)

    print(f"active_tasks {ansys_tasks}", flush=True)


def delete_task(task_name):
    command = fr'schtasks /DELETE /TN "AnsysDownloader\{task_name}" /f'  # /f - silent
    subprocess.check_output(command, shell=True)


def schedule_task(settings_file):
    unpack_days = {
        "mo": "MON",
        "tu": "TUE",
        "we": "WED",
        "th": "THU",
        "fr": "FRI",
        "sa": "SAT",
        "su": "SUN"
    }

    with open(settings_file) as file:
        settings = json.load(file)

    command = (fr'schtasks /CREATE /TN "AnsysDownloader\{settings["version"]}" /TR "{backend_exe} -p {settings_file}"' +
               fr' /d {",".join(unpack_days[day] for day in settings["days"])} /sc WEEKLY /st {settings["time"]} /f')

    subprocess.check_output(command, shell=True)


def install_once(settings_file):
    command = f'{backend_exe} -p "{settings_file}"'
    subprocess.call(command, shell=True)


def start():
    print('Python started from NODE.JS', flush=True)


def stop_run():
    print('Python stopped from NODE.JS', flush=True)
    exit()


start()
# command list
while True:
    line = sys.stdin.readline()
    if "get_active_tasks" in line:
        get_active_schtasks()
    elif "delete_task" in line:
        task = line.split()[1]
        delete_task(task)
    elif "exit" in line:
        stop_run()
    elif "schedule_task" in line:
        file_name = " ".join(line.split()[1:])
        schedule_task(file_name)
    elif "install_once" in line:
        file_name = " ".join(line.split()[1:])
        install_once(file_name)
    elif line:
        print('unrecognized command', flush=True)
