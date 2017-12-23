import re


def validate_ip_str(ip):
    match = re.match("^(\d{1,3})\.(\d{1,3})\.(\d{1,3})\.(\d{1,3})$", ip)
    if not match:
        return False
    quad = []
    for number in match.groups():
        if len(number) > 1 and number[0] == '0':
            return False
        quad.append(int(number))
    if quad[0] < 1:
        return False
    for number in quad:
        if number > 255 or number < 0:
            return False
    return True
