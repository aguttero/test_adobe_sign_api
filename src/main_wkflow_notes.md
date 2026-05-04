
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