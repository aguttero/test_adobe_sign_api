
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
* sync_groups()
    * api.fetch_all_groups()
    * get_token_manager().get_token()
BUG 
2026-05-05 08:40:56,725 [DEBUG] main.sync_groups — Group list len: 12
2026-05-05 08:40:56,725 [ERROR] main.sync_groups — Failed to sync groups: name 'convert_to_sqlite_date' is not defined


TODO Revisar y definir jerarquia de error handling
TODO Refator _get_token_manager que está en API . y refresh TOKEN que llama a API desde AUTH

## Sync Users
* sync_users()

## Sync Agreements
* sync_agreements()

TODO Context Caching
TODO Two-tier routing
TODO Batch processing -> Documentation 50% discount