
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
## Updates all groups
* sync_groups() ok
    * api.fetch_all_groups()
        * get_token_manager().get_token()
    * models.parse_groups(api_list)
        * convert_to_sqlite_date
    *db.upsert_groups(parsed_groups) (session.merge)


TODO Revisar y definir jerarquia de error handling
TODO Agregar error handling a las funciones que no tienen
TODO Refator _get_token_manager que está en API . y refresh TOKEN que llama a API desde AUTH

## Sync Workflows
* sync_workflows
    * api.fetch_all_workflows()
        * get_token_manager().get_token()
    * models.parse_workflows(api_workflow_list)
    * db.upsert_workflows(parsed_workflows)
    

## Sync Users
## Updates all users
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
## Updates agreements for valid users in given date range
* sync_agreements()
    * db.get_all_users(exclude_status="INVALID_USER")
    BUG
    * api.search_agreements(x,y,z)

BUG
  File "/Users/alejandroguttero/code_imac/test_adobesign_api/src/main.py", line 201, in sync_agreements
    total_users, users_with_zero, users_with_agr = sync_agreements_for_users(all_users, date_range_start, date_range_end)
                                                   ^^^^^^^^^^^^^^^^^^^^^^^^^
NameError: name 'sync_agreements_for_users' is not defined


IA TOKENS:
TODO Context Caching
TODO Two-tier routing
TODO Batch processing -> Documentation 50% discount

* sync_agreements()
    db.get all valid users
    for each user
        search agreement
            if user invalid
                update db user status
        transform
        persist agreements
            normalize
            persist signers
