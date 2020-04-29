import json
import logging
import os
import pathlib
import re
import subprocess
import threading
import time
import xml.etree.ElementTree as ET
from collections import OrderedDict
from datetime import datetime

import requests
import wx

import set_log
from downloader_ui_src import Ansys_Beta_Downloader_UI

artifactory_dict = OrderedDict([
    ('Austin', r'http://ausatsrv01.ansys.com:8080/artifactory'),
    ('Boulder', r'http://bouatsrv01:8080/artifactory'),
    ('Canonsburg', r'http://canartifactory.ansys.com:8080/artifactory'),
    ('Concord', r'http://convmartifact.win.ansys.com:8080/artifactory'),
    ('Darmstadt', r'http://darvmartifact.win.ansys.com:8080/artifactory'),
    ('Evanston', r'http://evavmartifact:8080/artifactory'),
    ('Gothenburg', r'http://gotvmartifact1:8080/artifactory'),
    ('Hannover', r'http://hanartifact1.ansys.com:8080/artifactory'),
    ('Horsham', r'http://horvmartifact1.ansys.com:8080/artifactory'),
    ('Lebanon', r'http://lebartifactory.win.ansys.com:8080/artifactory'),
    ('Lyon', r'http://lyovmartifact.win.ansys.com:8080/artifactory'),
    ('MiltonPark', r'http://milvmartifact.win.ansys.com:8080/artifactory'),
    ('Otterfing', r'http://ottvmartifact.win.ansys.com:8080/artifactory'),
    ('Pune', r'http://punvmartifact.win.ansys.com:8080/artifactory'),
    ('Sheffield', r'http://shfvmartifact.win.ansys.com:8080/artifactory'),
    ('SanJose', r'http://sjoartsrv01.ansys.com:8080/artifactory'),
    ('Waterloo', r'http://watatsrv01.ansys.com:8080/artifactory')
])


# signal - status bar
NEW_SIGNAL_EVT_BAR = wx.NewEventType()
SIGNAL_EVT_BAR = wx.PyEventBinder(NEW_SIGNAL_EVT_BAR, 1)


class SignalEvent(wx.PyCommandEvent):
    """Event to signal that we are ready to update the plot"""
    def __init__(self, etype, eid):
        """Creates the event object"""
        wx.PyCommandEvent.__init__(self, etype, eid)


class FlashStatusBarThread(threading.Thread):
    def __init__(self, parent):
        """
        @param parent: The gui object that should receive the value
        """
        threading.Thread.__init__(self)
        self._parent = parent

    def run(self):
        """Overrides Thread.run. Don't call this directly its called internally
        when you call Thread.start().

        alternates the color of the status bar for run_sec (6s) to take attention
        at the end clears the status message
        """

        if self._parent.bar_level == "i":
            alternating_color = wx.GREEN
        elif self._parent.bar_level == "!":
            alternating_color = wx.RED

        run_sec = 6
        for i in range(run_sec*2):
            self._parent.bar_color = wx.WHITE if i % 2 == 0 else alternating_color

            if i == run_sec*2 - 1:
                self._parent.bar_text = ""
                self._parent.bar_color = wx.WHITE

            evt = SignalEvent(NEW_SIGNAL_EVT_BAR, -1)
            wx.PostEvent(self._parent, evt)

            time.sleep(0.5)


class MainWindow(Ansys_Beta_Downloader_UI):
    def __init__(self, parent):
        Ansys_Beta_Downloader_UI.__init__(self, parent)

        set_log.set_logger()

        self.username_text.Value = os.environ["USERNAME"]
        self.download_path_textbox.Value = os.environ["TEMP"]
        self.install_path_textbox.Value = self._get_previous_edt_path()
        appdata = os.environ["APPDATA"]
        self.settings_folder = os.path.join(appdata, "build_downloader")

        if not os.path.isdir(self.settings_folder):
            os.mkdir(self.settings_folder)

        self.days_checkboxes = {"mo": self.mo_check,
                                "tu": self.tu_check,
                                "we": self.we_check,
                                "th": self.th_check,
                                "fr": self.fr_check,
                                "sa": self.sa_check,
                                "su": self.su_check}

        # setup tasks viewlist
        self.schtasks_viewlist.AppendTextColumn('Product', width=60)
        self.schtasks_viewlist.AppendTextColumn('Version', width=50)
        self.schtasks_viewlist.AppendTextColumn('Schedule', width=175)
        self.get_active_schtasks()

        # todo create a directory when execute (os.makedirs())if not exists if user enters path manually
        self._init_combobox(artifactory_dict.keys(), self.artifactory_dropmenu, "Otterfing")
        self.artifacts_dict = {}

        self.password_json = os.path.join(self.settings_folder, "pass.json")
        if os.path.isfile(self.password_json):
            with open(self.password_json) as file:
                self.password_dict = json.load(file)
        else:
            self.password_dict = {}

        # bind custom event to invoke function on_signal
        self.Bind(SIGNAL_EVT_BAR, self.set_status_bar)

    def post_init(self):
        """
        Function invoked right after __init__ to get settings and retrieve server data.
        This is required to show the user in statusbar that we are grabbing some data from server
        and not simply hanging
        :return:
        """
        if not self.read_settings():
            # file with defaults does not exist
            self.time_picker.Value = datetime.strptime("23:00:00", '%H:%M:%S')
            self.populate_password()
        else:
            self.get_artifacts_info()

    def set_status_bar(self, _unused_event=None):
        """
        This function is bound to the event that serves to flash status bar
        :param _unused_event: used only by UI
        :return: None
        """
        self.status_bar.SetStatusText(self.bar_text)
        self.status_bar.SetBackgroundColour(self.bar_color)
        self.status_bar.Refresh()

    def save_settings(self, settings_file="default_settings"):
        """
        Function to save current configuration of settings to the file
        :param settings_file: file name to write settings
        :return: settings_path: path to the settings file
        """
        setting_dict = {
            "install_path": self.install_path_textbox.Value,
            "username": self.username_text.Value,
            "artifactory": self.artifactory_dropmenu.Value,
            "password": self.password.Value,
            "delete_zip": self.delete_zip_check.Value,
            "download_path": self.download_path_textbox.Value,
            "version": self.version_dropmenu.Value,
            "wb_flags": self.wb_flags_text.Value,
            "days": [key for key, val in self.days_checkboxes.items() if val.Value],
            "time": self.time_picker.Value.FormatISOTime()
        }

        settings_path = os.path.join(self.settings_folder, settings_file + ".json")
        with open(settings_path, "w") as file:
            json.dump(setting_dict, file, indent=4)

        return settings_path

    def read_settings(self, settings_file="default_settings"):
        """
        Function to read settings and fill the UI
        :param settings_file: file name from which to read settings
        :return: False if settings_file does not exist else True
        """
        settings_path = os.path.join(self.settings_folder, settings_file + ".json")

        if not os.path.isfile(settings_path):
            return False

        with open(settings_path, "r") as file:
            setting_dict = json.load(file)

        self.install_path_textbox.Value = setting_dict["install_path"]
        self.username_text.Value = setting_dict["username"]
        self.artifactory_dropmenu.Value = setting_dict["artifactory"]
        self.password.Value = setting_dict["password"]
        self.delete_zip_check.Value = setting_dict["delete_zip"]
        self.download_path_textbox.Value = setting_dict["download_path"]
        self.version_dropmenu.Value = setting_dict["version"]
        self.wb_flags_text.Value = setting_dict["wb_flags"]
        self.time_picker.Value = datetime.strptime(setting_dict["time"], '%H:%M')

        for day in setting_dict["days"]:
            self.days_checkboxes[day].Value = True

        return True

    def add_status_msg(self, msg="", level="i"):
        """
        Function that creates a thread to add a status bar message with alternating color to take attention of the user
        :param msg: str, message text
        :param level: either "i" as information for green color or "!" as error for red color
        :return: None
        """
        self.bar_text = msg
        self.bar_level = level
        self.bar_color = wx.WHITE

        if msg:
            if level == "i":
                logging.info(msg)
            elif level == "!":
                logging.error(msg)

        # start a thread to update status bar
        self.worker = FlashStatusBarThread(self)
        self.worker.start()

    def set_install_path(self, _unused_event):
        """Invoked when clicked on "..." set_path_button."""
        path = self._path_dialogue("Install")
        if path:
            self.install_path_textbox.Value = path

    def set_download_path(self, _unused_event):
        """Invoked when clicked on "..." set_path_button."""
        path = self._path_dialogue("Download")
        if path:
            self.download_path_textbox.Value = path

    def save_question(self, event):
        """
            Function is fired up when you leave field of entering password:
            Updates password dictionary and possibly json file
            Runs get_artifacts_info to get available versions
        """
        event.Skip()  # need to skip, otherwise stuck on field

        # erase_pass: password key exists and user wants to delete it, thus question is needed
        erase_pass = not self.password.Value and self.password_dict.get(self.artifactory_dropmenu.Value, "")
        password_not_changed = self.password.Value == self.password_dict.get(self.artifactory_dropmenu.Value, "")

        if (not self.password.Value or password_not_changed) and not erase_pass:
            return

        answer = self._add_message("Do you want to save password for {}?".format(self.artifactory_dropmenu.Value),
                                   "Save password?", "?")

        if answer == wx.ID_YES:
            self.password_dict[self.artifactory_dropmenu.Value] = self.password.Value
            with open(self.password_json, "w") as file:
                json.dump(self.password_dict, file)

        self.get_artifacts_info()

    def save_default_click(self, _unused_event=None):
        self.save_settings()

    def populate_password(self, _unused_event=None):
        """
            Callback on change of artifact drop menu
            Fills the password field and calls get_artifacts_info
        """
        self.password.Value = self.password_dict.get(self.artifactory_dropmenu.Value, "")
        self.get_artifacts_info()

    def get_artifacts_info(self, _unused_event=None):
        """
            Function is fired on start of the UI or when Artifactory value is changed in drop down menu.
            Populate arifact_dict with versions of WB and EDT available on selected artifactory.
            Updates UI with these versions.
            :return None in case if we catch any HTTP error eg 401
        """
        self._init_combobox([], self.version_dropmenu)

        server = artifactory_dict[self.artifactory_dropmenu.Value]
        username = self.username_text.Value
        password = self.password.Value

        if not username or not password:
            self.add_status_msg("Please provide username and artifactory password", "!")
            return

        self.status_bar.SetStatusText("Connecting to server...")

        try:
            with requests.get(server + "/api/repositories", auth=(username, password),
                              timeout=30) as url_request:
                artifacts_list = json.loads(url_request.text)
        except requests.exceptions.ReadTimeout:
            self.add_status_msg("Timeout on connection, please verify your username and password for {}".format(
                self.artifactory_dropmenu.Value), "!")
            return
        except requests.exceptions.ConnectionError:
            self.add_status_msg("Connection error, please verify that you are on VPN".format(
                self.artifactory_dropmenu.Value), "!")
            return

        self.status_bar.SetStatusText("")

        # catch 401 for bad credentials or similar
        if url_request.status_code != 200:
            if url_request.status_code == 401:
                self.add_status_msg("Bad credentials, please verify your username and password for {}".format(
                    self.artifactory_dropmenu.Value), "!")
            else:
                self.add_status_msg(artifacts_list["errors"][0]["message"], "!")
            return

        # fill the dictionary with EBU and WB keys since builds could be different
        self.artifacts_dict = {}
        for artifact in artifacts_list:
            repo = artifact["key"]
            if "EBU_Certified" in repo:
                version = repo.split("_")[0] + "_EDT"
                if version not in self.artifacts_dict:
                    self.artifacts_dict[version] = repo
            elif "Certified" in repo and "Licensing" not in repo:
                version = repo.split("_")[0] + "_WB"
                if version not in self.artifacts_dict:
                    self.artifacts_dict[version] = repo

        versions = list(self.artifacts_dict.keys())
        versions.sort(key=lambda x: x[1:6])
        self._init_combobox(versions, self.version_dropmenu, sorted(self.artifacts_dict.keys())[-1])

    def get_active_schtasks(self):
        """
        Function to get schtasks that are already scheduled for EDT and WB
        UI is updated with this info
        """

        command = r"schtasks /query /xml"
        all_tasks = subprocess.check_output(command, shell=True).decode("ascii", errors="ignore")
        all_tasks = all_tasks.split("\r\n\r\n\r\n")

        for task in all_tasks:
            if "AnsysDownloader" in task:
                task_data_dict = self.get_task_details(task)
                schedule_time = ", ".join(task_data_dict["days"]) + " at " + task_data_dict["time"]
                self.schtasks_viewlist.AppendItem([task_data_dict["product"],
                                                  task_data_dict["version"],
                                                  schedule_time])

    def install_once_click(self, _unused_event=None):
        """
        Invoked when user clicks Install once button
        :param _unused_event: default arg
        :return: None
        """
        settings_file = self.save_settings("one_time_install_" + self.version_dropmenu.Value)
        threading.Thread(target=self.submit_batch_thread, daemon=True, args=(settings_file,)).start()
        self.add_status_msg("Download and installation was successfully started", "i")

    @staticmethod
    def submit_batch_thread(settings_file):
        command = f'python.exe downloader_backend.py -p {settings_file}'.split()
        subprocess.call(command)

    @staticmethod
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

    @staticmethod
    def _get_previous_edt_path():
        """
        :return path of EDT installation based on environment variable or empty string if no env var found
        """
        all_vars = os.environ
        env_var = ""
        for key in all_vars:
            if "ANSYSEM" in key:
                env_var = all_vars[key]

        if env_var:
            edt_root = str(pathlib.Path(env_var).parent.parent.parent)
            return edt_root
        else:
            return ""

    @staticmethod
    def _path_dialogue(which_dir):
        """
        Creates a dialogue where user can select directory
        :param which_dir: name of the required path (Install or Download)
        :return: (str/bool) path to the file or False if user closed the dialogue
        """
        get_dir_dialogue = wx.DirDialog(None, "Choose {} directory:".format(which_dir), style=wx.DD_DEFAULT_STYLE)
        if get_dir_dialogue.ShowModal() == wx.ID_OK:
            path = get_dir_dialogue.GetPath()
            get_dir_dialogue.Destroy()
            return path
        else:
            get_dir_dialogue.Destroy()
            return False

    @staticmethod
    def _init_combobox(entry_list, combobox, default_value=''):
        """
        Fills a wx.Combobox element with the entries in a list
        Input parameters
        :param entry_list: List of text entries to appear in the combobox element
        :param combobox: object pointing to the combobox element
        :param default_value: (optional default value (must be present in the entry list, otherwise will be ignored)

        Outputs
        :return: None
        """
        combobox.Clear()
        index = 0
        for i, v in enumerate(list(entry_list)):
            if v == default_value:
                index = i
            combobox.Append(v)
        combobox.SetSelection(index)

    @staticmethod
    def _add_message(message, title="", icon="?"):
        """
        Create a dialog with different set of buttons
        :param message: Message you want to show
        :param title:
        :param icon: depending on the input will create either question dialogue (?), error (!) or just information
        :return Answer of the user eg wx.OK
        """

        if icon == "?":
            icon = wx.YES | wx.NO | wx.ICON_QUESTION
        elif icon == "!":
            icon = wx.OK | wx.ICON_ERROR
        else:
            icon = wx.OK | wx.ICON_INFORMATION

        dlg_qdel = wx.MessageDialog(None, message, title, icon)
        result = dlg_qdel.ShowModal()
        dlg_qdel.Destroy()

        return result


def main():
    """Main function to generate UI. Validate that only one instance is opened."""
    app = wx.App()
    ui = MainWindow(None)
    ui.Show()
    ui.post_init()
    app.MainLoop()


if __name__ == '__main__':
    main()
