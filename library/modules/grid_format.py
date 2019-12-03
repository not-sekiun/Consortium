def chunks(l, n):
    for i in range(0, len(l), n):
        yield l[i:i + n]


def main(list_to_format, num):
    longest = len(max(list_to_format, key=len)) + 1
    even_list = list(chunks(list_to_format, num))
    for row in even_list:
        for element in row:
            row[row.index(element)] = '[' + element + ']' + (longest - len(element)) * ' '
    return even_list
