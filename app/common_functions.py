def convert_to_list(string):
    result = ''
    elems_raw = string.strip().split(',')
    for elem in elems_raw:
        if '-' in elem:
            start, end = elem.split('-')
            elem = ','.join(
                str(num) for num in range(int(start), int(end) + 1)
                )
        elif elem == '':
            return None
        if result:
            result += ',' + elem
        else:
            result += elem
    return result.split(',')
