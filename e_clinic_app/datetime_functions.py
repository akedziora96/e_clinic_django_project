from datetime import datetime, timedelta

WEEKDAYS = {
    1: "Monday",
    2: "Tuesday",
    3: "Wednesday",
    4: "Thursday",
    5: "Friday",
    6: "Saturday"
}


def get_weekdays_names(dates):
    return {WEEKDAYS[date.weekday() + 1]: date.strftime("%d.%m") for date in dates}


def get_week_start_and_end(week_offset=0):
    day_offset = 7 * week_offset
    now = datetime.now()
    offset_now = now + timedelta(days=day_offset)
    offset_monday = offset_now - timedelta(days=offset_now.weekday())
    offset_saturday = offset_monday + timedelta(days=5)

    if offset_saturday < datetime.today():
        current_week_monday = now - timedelta(days=now.weekday())
        current_week_saturday = current_week_monday + timedelta(days=5)
        return current_week_monday, current_week_saturday

    return offset_monday, offset_saturday


if __name__ == '__main__':
    print(get_week_start_and_end(1))
