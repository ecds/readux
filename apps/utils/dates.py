from edtf.convert import struct_time_to_jd
from datetime import date
import time


def date_to_jd(d: date) -> float:
    return struct_time_to_jd(time.strptime(d.strftime("%Y-%m-%d"), "%Y-%m-%d"))
