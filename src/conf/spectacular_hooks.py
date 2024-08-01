def api_ordering(endpoints):
    method_ordering_mapper = {"GET": 0, "POST": 1, "PUT": 2, "PATCH": 3, "DELETE": 4}
    endpoints = sorted(endpoints, key=lambda x: [x[0], method_ordering_mapper[x[2]]])
    return endpoints
