from django.apps import AppConfig


class CommonConfig(AppConfig):
    name = 'common'

    def ready(self):
        import sys
        if 'runserver' not in sys.argv:
            return True
            
        from django.db import connections
        from django.db.utils import OperationalError
        
        try:
            db_conn = connections['default']
            db_conn.cursor()
            print("\n" + "="*50)
            print("  MONGODB CONNECTED SUCCESSFULLY: FitMitra_DB")
            print("="*50 + "\n")
        except OperationalError:
            print("\n" + "="*50)
            print("  MONGODB CONNECTION FAILED")
            print("="*50 + "\n")
