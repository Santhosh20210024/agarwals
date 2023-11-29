def construct_file_url(*args):
    list_of_items = []
    for arg in args:
        list_of_items.append(arg)

    formatted_url = '/'.join(list_of_items)
    return formatted_url