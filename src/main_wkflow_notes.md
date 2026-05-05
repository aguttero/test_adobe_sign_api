
# Main () Workflow
## Init Logger config and run and time stamps
* logger tested OK -> need to run first: line 33 logger = logging.getLogger(__name__)
* def initialize_app() -> Triggers logging configuration OK

## Prepare the date range for the sync process
* prepare_date_range - OK

## Insert SyncHistory record at the start of the run
* db.insert_sync_history OK

## Get initial agreement count for rollback tracking
* db.get_agreement_count() OK

## Sync Groups
* sync_groups() ok
    * api.fetch_all_groups()
    * get_token_manager().get_token()
    * models.parse_groups(api_list)
        * convert_to_sqlite_date
    *db.upsert_groups(parsed_groups) (session.merge)


TODO Revisar y definir jerarquia de error handling
TODO Agregar error handling a las funciones que no tienen
TODO Refator _get_token_manager que está en API . y refresh TOKEN que llama a API desde AUTH

## Sync Users
* sync_users()
    * api.fetch_all_users() -> List DICT
    * db.transform_user_list_keys(api_user_list)
    TODO Parse users en Models (igual que groups)
    * db.insert_new_items_by_email_key(transformed_user_list)
        * db.get_existing_emails() existing_emails
        * db.filter_new_users (existing_emails)
        * db.bulk_insert_list (new_users_list)
TODO Revisar y definir jerarquia de error handling
TODO Agregar error handling a las funciones que no tienen
TODO Revisar logica de usuarios archivados
TODO crear funcion upsert Users


## Sync Agreements
* sync_agreements()

IA TOKENS:
TODO Context Caching
TODO Two-tier routing
TODO Batch processing -> Documentation 50% discount