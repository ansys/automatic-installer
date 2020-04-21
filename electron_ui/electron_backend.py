import subprocess
import sys
import re
import xml.etree.ElementTree as ET


# FUNCTIONS
def get_task_details(task):
    """
    Function that extracts parameters of individual task
    :param task: XML string contained all data about the task
    :return task_data_dict = {"days": [],
                              "time": "00:00",
                              "product": "EDT",
                              "version": "v201"}
    """

    task_data_dict = {"days": [],
                      "time": "00:00",
                      "product": "EDT",
                      "version": "v201"}

    task = "\n".join(task.replace("\r\n", "").split("\r")[1:])  # remove empty lines

    schtasks = ET.fromstring(task)
    ns = {"win": re.search("{(.*)}Task", schtasks.tag).group(1)}  # name space

    calendar_trig = schtasks.find("win:Triggers/win:CalendarTrigger", ns)
    start_boundary = calendar_trig.find("win:StartBoundary", ns).text
    days = calendar_trig.find("win:ScheduleByWeek/win:DaysOfWeek", ns)
    for day in days:
        day_name = day.tag.split("}")[1][:3]
        task_data_dict["days"].append(day_name)

    task_data_dict["time"] = start_boundary.split("T")[1][:-3]

    uri = schtasks.find("win:RegistrationInfo/win:URI", ns)
    name = uri.text.split("\\")[2]
    task_data_dict["product"], task_data_dict["version"] = name.split("_")
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
    for task in all_tasks:
        if "AnsysDownloader" in task:
            task_data_dict = get_task_details(task)
            task_data_dict["schedule_time"] = ", ".join(task_data_dict["days"]) + " at " + task_data_dict["time"]
            ansys_tasks.append(task_data_dict)

    print(f"active_tasks {ansys_tasks}", flush=True)


def start():
    print('I STARTED and asked to install FROM WITHIN NODE.JS', flush=True)
    with open(r"D:\1.txt", "w") as file:
        file.write("Start install once\n")


def respond():
    print('schedule update man', flush=True)
    with open(r"D:\1.txt", "a") as file:
        file.write('I GOT hello FROM NODE.JS -> HI THERE EXAMPLE ANALYZER\n')


def stop_run():
    print('I GOT exit FROM NODE.JS -> I STOPPED FROM WITHIN NODE.JS', flush=True)
    exit()


# CODE

while True:
    line = sys.stdin.readline()
    if "get_active_tasks" in line:
        get_active_schtasks()

    elif "exit" in line:
        stop_run()
    elif "schedule_update" in line:
        respond()
    elif "install_once" in line:
        start()
    elif line:
        print('dunno')
