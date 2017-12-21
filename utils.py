# (c) Baltasar (c) 2017 MIT License <baltasarq@gmail.com>

import time


def create_file_name(user_name, prefix, item_name):
    name_part = (prefix + "_" + item_name).replace(' ', '_').lower()
    export_time = time.localtime()
    str_export_time = str.format("{0:02d}_{1:02d}_{2:02d}",
                                 export_time.tm_year, export_time.tm_mon, export_time.tm_mday)
    str_export_time += "-" + str.format("{0:02d}_{1:02d}_{2:02d}",
                                        export_time.tm_hour, export_time.tm_min, export_time.tm_sec)
    toret = user_name + "-" + name_part + "-" + str_export_time
    toret = toret.replace('/', '').replace('\\', '')
    toret = toret.encode("ascii", "ignore")
    return toret
