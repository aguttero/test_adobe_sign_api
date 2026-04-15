from datetime import datetime, timedelta

# TODO GET LAST RANGE END DATE
last_end_date_str = "2026-03-01T00:00:00Z" # Read this date_str from DB Exec Log
new_start_range_date_str = last_end_date_str
new_range_end_date = datetime.fromisoformat(last_end_date_str) + timedelta(days=7)
print ("new_range_end_date:", new_range_end_date)
new_range_end_date_str = f"{new_range_end_date.date()}T00:00:00Z"
print ("new_start_range_date_str:", new_range_end_date_str)

# VALIDATE search range is in the past
datetime_today = datetime.today()
print ("datetime_today:", datetime_today)
naive_new_end_range_date = datetime.fromisoformat(new_range_end_date_str.replace("T00:00:00Z"," 00:00:00"))
print ("- - - - ")
if datetime_today >= naive_new_end_range_date:
    print (f"OK to run search. Naive range end datetime: {naive_new_end_range_date}")
    #logger.debug(f"OK Range end date in the past. Naive range end datetime: {naive_new_end_range_date}")
else:
    print ("ERROR - Reschedule Chron")
    #logger.critical(f"RUM DATE ERROR: Search Range NOT in the PAST - CHECK MAIN RUN CHRON. Naive range end datetime > dateime.now(): {naive_new_end_range_date}")
