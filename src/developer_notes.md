## Documentation
https://secure.na1.adobesign.com/public/docs/restapi/v6
https://github.com/adobe-sign/rest-api-sample
https://github.com/adobe-sign/AdobeSign-OpenAPI

## Agreement Endpoints
1. Get /agreements x-api-user email:
```json
{
    "userAgreementList": [
        {
            "displayDate": "2026-03-23T19:06:40Z",
            "name": "Agreement Name",
            "id": "Agreement ID",
            "status": "SIGNED",
            "type": "AGREEMENT",

            "displayParticipantSetInfos": [
                    {
                        "displayUserSetMemberInfos": [
                            {
                                "email": "email@email",
                                "company": "Company Name",
                                "fullName": "Fullname",
                                "deliverableEmail": true
                            }
                        ]
                    }
                ],
        },
    ],
    "page": {
        "nextCursor": "cursor id"
     }
}```

2. /Search -> Todos los agreements en que participaste - user id, agreement id, role, participant list
    Dates:
        "createdDate": "2018-07-17T16:28:54-07:00",
        "modifiedDate": "2018-07-17T16:42:54-07:00"
        "status"
```json
{
    "agreementAssetsResults": {

        "totalHits": 24,
        "status": {
            "code": 200,
            "message": null
        },
        "searchPageInfo": {
            "nextIndex": null
        },
        "agreementAssetsResultList": [
            {
                "role": ["SENDER"],
                "type": "AGREEMENT",
                "userId":"",
                "participantList": [],
                "createdDate": "2026-03-09T11:15:32-07:00",
                "modifiedDate": "2026-03-09T12:28:28-07:00",
                "name": "Agreement Name",
                "id": "agreement id",
                "workflowId": "workflow id",
                "status": "SIGNED",
                "expirationDate": null
            }
        ]
    }
}
```

3. /Get Agreement info
 ```json
{ 
    "id": "Agreement id",
    "name": "Agreement name",
    "type": "AGREEMENT",
    "groupId": "Group ID",
    "workflowId": "Wf iD", // de match con la lista de WFs
    "message": "mensaje al firmante",
    "participantSetsInfo": ["memberId,memeberInfos:[{email, name, id?Adobe?}, role, order, label"],
    "senderEmail": "email",
    "createdDate": "2026-03-09T18:15:32Z",
    "lastEventDate": "2026-03-09T19:28:27Z",
    "status": "SIGNED"
},
{
    "workflowId": "wf id",
    "participantSetsInfo_Id": "participant setinfo ide",
}
{
    "email": "email",
    "name": "name",
    "id": "user_id",
},
{
    "email": "d",
    "deliverableEmail": true,
    "name": "gte de compras",
    "id": "user_id",
}

## DB SQLite

```SQL DDL
CREATE TABLE user_account (
	id INTEGER NOT NULL, 
	email VARCHAR NOT NULL, 
	group_id VARCHAR, 
	first_name VARCHAR, 
	last_name VARCHAR, 
	job_area VARCHAR, 
	job_title VARCHAR, 
	status VARCHAR, 
	adbe_sign_id VARCHAR NOT NULL, 
	last_sync DATE NOT NULL, 
	PRIMARY KEY (id)
)
CREATE UNIQUE INDEX ix_user_account_email ON user_account (email)
CREATE UNIQUE INDEX ix_user_account_adbe_sign_id ON user_account (adbe_sign_id)

CREATE TABLE agreement (
	id INTEGER NOT NULL, 
	agreement_id VARCHAR NOT NULL, 
	user_id INTEGER, 
	display_date DATE NOT NULL, 
	name VARCHAR NOT NULL, 
	type VARCHAR NOT NULL, 
	status VARCHAR NOT NULL, 
	workflow_id VARCHAR, 
	group_id VARCHAR NOT NULL, 
	created_date DATE NOT NULL, 
	last_event_date DATE NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(user_id) REFERENCES user_account (id)
)
CREATE UNIQUE INDEX ix_agreement_agreement_id ON agreement (agreement_id)

CREATE TABLE sync_history (
	id INTEGER NOT NULL, 
	run_date DATE NOT NULL, 
	range_start VARCHAR NOT NULL, 
	range_end VARCHAR NOT NULL, 
	agreements_found INTEGER NOT NULL, 
	sync_ok BOOLEAN NOT NULL, 
	PRIMARY KEY (id)
)


```