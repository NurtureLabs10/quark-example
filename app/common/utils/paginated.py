def paginated(data, limit, page):
    limit = int(limit) if limit else 9
    page = int(page) if page else 1
    start_index = (page - 1) * limit
    end_index = page * limit
    return data[start_index: end_index]
