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

def make_choices(model, choiced_attr, order_by=None):
    if order_by:
        order_by = getattr(model, order_by)
    return [
        (row.id, getattr(row, choiced_attr))
         for row in model.query.order_by(order_by).all()
        ]
