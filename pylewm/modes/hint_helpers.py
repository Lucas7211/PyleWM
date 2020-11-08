
def create_hints(item_list, hintkeys):
    depth = 1
    key_count = len(hintkeys)

    depth_count = float(len(item_list))
    while depth_count > key_count:
        depth += 1
        depth_count /= float(key_count)

    for i, item in enumerate(item_list):
        item.hint = ""
        n = i
        for d in range(0, depth):
            item.hint += hintkeys[n % key_count]
            n = int(n / key_count)