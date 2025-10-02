Traceback (most recent call last):
  File "C:\Users\joger\AppData\Local\Programs\Python\Python313\Lib\site-packages\django\db\backends\base\base.py", line 289, in ensure_connection
    self.connect()
    ~~~~~~~~~~~~^^
  File "C:\Users\joger\AppData\Local\Programs\Python\Python313\Lib\site-packages\django\utils\asyncio.py", line 26, in inner
    return func(*args, **kwargs)
  File "C:\Users\joger\AppData\Local\Programs\Python\Python313\Lib\site-packages\django\db\backends\base\base.py", line 270, in connect
    self.connection = self.get_new_connection(conn_params)
                      ~~~~~~~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^
  File "C:\Users\joger\AppData\Local\Programs\Python\Python313\Lib\site-packages\django\utils\asyncio.py", line 26, in inner
    return func(*args, **kwargs)
  File "C:\Users\joger\AppData\Local\Programs\Python\Python313\Lib\site-packages\django\db\backends\postgresql\base.py", line 275, in get_new_connection
    connection = self.Database.connect(**conn_params)
  File "C:\Users\joger\AppData\Local\Programs\Python\Python313\Lib\site-packages\psycopg2\__init__.py", line 135, in connect
    conn = _connect(dsn, connection_factory=connection_factory, **kwasync)
psycopg2.OperationalError: connection to server at "127.0.0.1", port 5432 failed: FATAL:  password authentication failed for user "postgres"


The above exception was the direct cause of the following exception:

Traceback (most recent call last):
  File "D:\Code\Azure Reports\azure_advisor_reports\manage.py", line 22, in <module>
    main()
    ~~~~^^
  File "D:\Code\Azure Reports\azure_advisor_reports\manage.py", line 18, in main
    execute_from_command_line(sys.argv)
    ~~~~~~~~~~~~~~~~~~~~~~~~~^^^^^^^^^^
  File "C:\Users\joger\AppData\Local\Programs\Python\Python313\Lib\site-packages\django\core\management\__init__.py", line 442, in execute_from_command_line
    utility.execute()
    ~~~~~~~~~~~~~~~^^
  File "C:\Users\joger\AppData\Local\Programs\Python\Python313\Lib\site-packages\django\core\management\__init__.py", line 436, in execute
    self.fetch_command(subcommand).run_from_argv(self.argv)
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~^^^^^^^^^^^
  File "C:\Users\joger\AppData\Local\Programs\Python\Python313\Lib\site-packages\django\core\management\base.py", line 412, in run_from_argv
    self.execute(*args, **cmd_options)
    ~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^
  File "C:\Users\joger\AppData\Local\Programs\Python\Python313\Lib\site-packages\django\core\management\commands\sqlmigrate.py", line 38, in execute
    return super().execute(*args, **options)
           ~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^
  File "C:\Users\joger\AppData\Local\Programs\Python\Python313\Lib\site-packages\django\core\management\base.py", line 458, in execute
    output = self.handle(*args, **options)
  File "C:\Users\joger\AppData\Local\Programs\Python\Python313\Lib\site-packages\django\core\management\commands\sqlmigrate.py", line 46, in handle
    loader = MigrationLoader(connection, replace_migrations=False)
  File "C:\Users\joger\AppData\Local\Programs\Python\Python313\Lib\site-packages\django\db\migrations\loader.py", line 58, in __init__
    self.build_graph()
    ~~~~~~~~~~~~~~~~^^
  File "C:\Users\joger\AppData\Local\Programs\Python\Python313\Lib\site-packages\django\db\migrations\loader.py", line 235, in build_graph
    self.applied_migrations = recorder.applied_migrations()
                              ~~~~~~~~~~~~~~~~~~~~~~~~~~~^^
  File "C:\Users\joger\AppData\Local\Programs\Python\Python313\Lib\site-packages\django\db\migrations\recorder.py", line 81, in applied_migrations
    if self.has_table():
       ~~~~~~~~~~~~~~^^
  File "C:\Users\joger\AppData\Local\Programs\Python\Python313\Lib\site-packages\django\db\migrations\recorder.py", line 57, in has_table
    with self.connection.cursor() as cursor:
         ~~~~~~~~~~~~~~~~~~~~~~^^
  File "C:\Users\joger\AppData\Local\Programs\Python\Python313\Lib\site-packages\django\utils\asyncio.py", line 26, in inner
    return func(*args, **kwargs)
  File "C:\Users\joger\AppData\Local\Programs\Python\Python313\Lib\site-packages\django\db\backends\base\base.py", line 330, in cursor
    return self._cursor()
           ~~~~~~~~~~~~^^
  File "C:\Users\joger\AppData\Local\Programs\Python\Python313\Lib\site-packages\django\db\backends\base\base.py", line 306, in _cursor
    self.ensure_connection()
    ~~~~~~~~~~~~~~~~~~~~~~^^
  File "C:\Users\joger\AppData\Local\Programs\Python\Python313\Lib\site-packages\django\utils\asyncio.py", line 26, in inner
    return func(*args, **kwargs)
  File "C:\Users\joger\AppData\Local\Programs\Python\Python313\Lib\site-packages\django\db\backends\base\base.py", line 288, in ensure_connection
    with self.wrap_database_errors:
         ^^^^^^^^^^^^^^^^^^^^^^^^^
  File "C:\Users\joger\AppData\Local\Programs\Python\Python313\Lib\site-packages\django\db\utils.py", line 91, in __exit__
    raise dj_exc_value.with_traceback(traceback) from exc_value
  File "C:\Users\joger\AppData\Local\Programs\Python\Python313\Lib\site-packages\django\db\backends\base\base.py", line 289, in ensure_connection
    self.connect()
    ~~~~~~~~~~~~^^
  File "C:\Users\joger\AppData\Local\Programs\Python\Python313\Lib\site-packages\django\utils\asyncio.py", line 26, in inner
    return func(*args, **kwargs)
  File "C:\Users\joger\AppData\Local\Programs\Python\Python313\Lib\site-packages\django\db\backends\base\base.py", line 270, in connect
    self.connection = self.get_new_connection(conn_params)
                      ~~~~~~~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^
  File "C:\Users\joger\AppData\Local\Programs\Python\Python313\Lib\site-packages\django\utils\asyncio.py", line 26, in inner
    return func(*args, **kwargs)
  File "C:\Users\joger\AppData\Local\Programs\Python\Python313\Lib\site-packages\django\db\backends\postgresql\base.py", line 275, in get_new_connection
    connection = self.Database.connect(**conn_params)
  File "C:\Users\joger\AppData\Local\Programs\Python\Python313\Lib\site-packages\psycopg2\__init__.py", line 135, in connect
    conn = _connect(dsn, connection_factory=connection_factory, **kwasync)
django.db.utils.OperationalError: connection to server at "127.0.0.1", port 5432 failed: FATAL:  password authentication failed for user "postgres"

