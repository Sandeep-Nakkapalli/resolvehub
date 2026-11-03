try:
    import pymysql

    pymysql.install_as_MySQLdb()
except ImportError:
    # SQLite-only development does not require the MySQL adapter.
    pass
