import tests.test_api as api
import tests.test_database as dbmgr

active_token = api.refresh_token()

result = api.fetch_users(active_token)

## Ejemplo captura de error de modulo API RAISE
# import api, db, alerts

def run_sync():
    try:
        users = api.fetch_users(active_token)
        dbmgr.save_users(users)
    except ConnectionError as e:
        # ALERTA PARA EL MANAGER
        print ("alerta critica en slack")
        # alerts.send_to_slack(f"Error Crítico: La sincronización falló por problemas de red: {e}")
    except Exception as e:
        print ("alerta inesperada en slack")
        # alerts.send_to_slack(f"🚨 Error Inesperado: {e}")
