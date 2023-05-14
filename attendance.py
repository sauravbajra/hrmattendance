#!/usr/bin/python3

"""

author @debendraoli

This script is used to automate attendance in hrm.ingnepal.com

Usage:
    python attendance.py

    If setting.ini file is not found, it will create one for you.
    Please fill up you credentials in setting.ini file.

    Credentials can also be passed as environment variable.
    fields: EMAIL, PASSWORD, LAST_ACTION, WORK_FROM_HOME_DAYS

Note:
    1. You can also use this script as a cron job.
    2. You can also use this script as a github action.
    3. You can also use this script as a docker container.

Cron job:
    For check in:
        1. Open terminal and type "crontab -e"
        2. Add this line `0 9 * * 1-5 python3 /path/to/attendance.py` and save it.
        3. This will run the script every weekday at 9:00 AM. Weekday are 1-5 (Monday to Friday)
    
    For check out:
        1. Open terminal and type "crontab -e"
        2. Add this line `0 18 * * 1-5 python3 /path/to/attendance.py` and save it.
        3. This will run the script every weekday at 6:00 PM. Weekday are 1-5 (Monday to Friday)

"""

import configparser
import json
import re
from datetime import datetime
from os import environ, path
from tkinter import messagebox
from urllib.parse import urlencode
from urllib.request import Request, urlopen


class Helper:
    def __init__(self):
        self._config = Helper.config_loader()
        config = {
            "email": environ.get("EMAIL", self._config.get("credentials", "email")),
            "pass": environ.get("PASSWORD", self._config.get("credentials", "password")),
            "last_action": environ.get("LAST_ACTION", self._config.get("state", "last_action")),
            "work_from_home_days": environ.get("WORK_FROM_HOME_DAYS", self._config.get("state", "work_from_home_days")),
        }
        self._last_action = config.get("last_action")
        self._home_days = config.get("work_from_home_days").split(",")
        self.url = "https://hrm.ingnepal.com/Attendance/QuickAttendanceRequest/QuickAttendance"
        self.headers = {
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/200.0.4430.72 Safari/537.36"
        }
        self.data = {
            "LoginID": config.get("email"),
            "LoginPassword": config.get("pass"),
            "IsWorkFromHome": self._is_work_from_home(),
            "Direction": self._next_action(),
            "Remarks": "",
            "RandomSeed": "",
        }

    @staticmethod
    def config_loader():
        config = configparser.ConfigParser()
        if path.exists("setting.ini"):
            config.read("setting.ini")
            return config
        config.add_section("credentials")
        config["credentials"]["email"] = "PUT_YOUR_HRM_EMAIL_HERE"
        config["credentials"]["password"] = "PUT_YOUR_HRM_PASSWORD_HERE"
        config.add_section("state")
        config["state"]["last_action"] = "Out"
        config["state"]["work_from_home_days"] = "mon,tue,wed"
        config["state"]["date"] = str(datetime.now())
        with open("setting.ini", "w") as configfile:
            config.write(configfile)
        messagebox.showinfo("Attendance", "Please fill up your credentials in setting.ini file.")
        exit(0)

    def _next_action(self):
        states = {"In": "Out", "Out": "In"}
        return states.get(self._last_action, "In")
    
    def _is_work_from_home(self):
        if datetime.now().strftime("%A").lower()[:3] in self._home_days:
            return True
        return False

    def _write_last_action(self):
        self._config["state"]["last_action"] = self._next_action()
        self._config["state"]["date"] = str(datetime.now())
        with open("setting.ini", "w") as config:
            self._config.write(config)

    def _get_require_data(self):
        try:
            req = Request(url=self.url, headers=self.headers)
            with urlopen(req) as res:
                cookie = (
                    res.info()
                    .get_all("Set-Cookie")[0]
                    .removeprefix("__RequestVerificationToken=")
                    .removesuffix("; path=/; HttpOnly")
                )
                regex = r'<input name="__RequestVerificationToken" type="hidden" value="(.+)" />'
                search_token = re.search(regex, res.read().decode("utf-8"))
                return f"__RequestVerificationToken={cookie}", search_token.groups()[0]
        except Exception:
            messagebox.showinfo("Attendance", "Something went wrong. Please try again later.")
            exit(1)

    def attend(self):
        cookie, token = self._get_require_data()
        self.headers["Cookie"] = cookie
        self.data["__RequestVerificationToken"] = token
        try:
            req = Request(url=self.url, headers=self.headers, data=urlencode(self.data).encode())
            with urlopen(req) as res:
                json_data = json.loads(res.read().decode("utf-8"))
                messagebox.showinfo("Attendance", json_data.get("Message"))
            self._write_last_action()
        except Exception:
            messagebox.showerror("Attendance", "Something went wrong. Please try again later.")
            exit(1)


helper = Helper()
helper.attend()
