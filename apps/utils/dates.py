from edtf.convert import struct_time_to_jd, jd_to_struct_time
from datetime import date, MINYEAR
import time


def date_to_jd(d: date) -> float:
    # Use explicit zero-padded formatting — strftime("%Y") does not zero-pad years
    # below 1000 on all platforms, causing strptime to reject the result.
    date_str = f"{d.year:04d}-{d.month:02d}-{d.day:02d}"
    return struct_time_to_jd(time.strptime(date_str, "%Y-%m-%d"))


def jd_to_date(jd: float) -> date | None:
    """Convert a Julian Day Number (float) back to a Python date.

    Returns None if the JD maps to a year outside Python's date range (e.g. year 0
    from EDTF astronomical year numbering, or any year before MINYEAR=1).
    """
    st = jd_to_struct_time(jd)
    if st.tm_year < MINYEAR:
        return None
    try:
        return date(st.tm_year, st.tm_mon, st.tm_mday)
    except ValueError:
        return None
