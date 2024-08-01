from django_hosts import host, patterns


host_patterns = patterns(
    "",
    host("api", "conf.urls.api", name="api"),
    host("admin", "conf.urls.admin", name="admin"),
)
