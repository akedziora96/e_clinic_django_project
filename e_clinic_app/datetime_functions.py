from datetime import datetime, timedelta


def get_monday(offset=0):
    now = datetime.now()
    now += timedelta(days=offset)
    monday = now - timedelta(days=now.weekday())
    return monday


def get_saturday(offset=0):
    monday = get_monday(offset)
    friday = monday + timedelta(days=5)
    return friday


if __name__ == '__main__':
    print(get_monday(7), get_saturday(7))
