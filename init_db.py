# -*- coding: utf-8 -*-
__author__ = 'songbowen'

from lib.attendance_logic import set_legal_check
from lib.attendance_logic import update_attendance_status


if __name__ == "__main__":
    for i in range(2, 120):
        set_legal_check(i)
        update_attendance_status(i)

